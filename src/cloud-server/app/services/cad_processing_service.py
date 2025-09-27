"""
CAD Processing Service for ArchBuilder.AI

Multi-format CAD file processing supporting DWG, DXF, IFC formats.
Provides geometric analysis, format conversion, and BIM intelligence.

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

import asyncio
import tempfile
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from io import BytesIO

import numpy as np
from pydantic import BaseModel
from structlog import get_logger

# CAD processing imports
try:
    import ezdxf
    from ezdxf import recover
    from ezdxf.math import Vec3
except ImportError:
    ezdxf = None
    logger.warning("ezdxf not available - DWG/DXF processing disabled")

try:
    import ifcopenshell
    import ifcopenshell.geom
except ImportError:
    ifcopenshell = None
    logger.warning("ifcopenshell not available - IFC processing disabled")

# 3D processing
try:
    import open3d as o3d
except ImportError:
    o3d = None
    logger.warning("open3d not available - 3D geometry processing disabled")

# Placeholder imports - adjust based on actual package structure
# from ..schemas.layout_schemas import Point2D, WallElement, DoorElement, WindowElement  
# from ..core.exceptions import ProcessingError, ValidationError
# from ..utils.geometry import GeometryUtils

# Temporary type definitions for standalone operation
from typing import List, Dict, Any

logger = get_logger(__name__)


class CADFormat(str, Enum):
    """Desteklenen CAD dosya formatları"""
    DWG = "dwg"
    DXF = "dxf"
    IFC = "ifc"
    PLY = "ply"
    OBJ = "obj"
    STL = "stl"


class ElementType(str, Enum):
    """CAD element tipleri"""
    WALL = "wall"
    DOOR = "door"
    WINDOW = "window"
    ROOM = "room"
    FURNITURE = "furniture"
    ANNOTATION = "annotation"
    DIMENSION = "dimension"


class CADElement(BaseModel):
    """CAD elementi temel sınıfı"""
    id: str
    type: ElementType
    layer: Optional[str] = None
    properties: Dict[str, Any] = {}
    geometry: Dict[str, Any] = {}
    material: Optional[str] = None
    
    class Config:
        extra = "allow"


class ProcessingResult(BaseModel):
    """CAD processing sonucu"""
    file_id: str
    format: CADFormat
    elements: List[CADElement]
    metadata: Dict[str, Any]
    processing_time_ms: int
    warnings: List[str] = []
    errors: List[str] = []


class CADProcessingService:
    """
    Multi-format CAD file processing service
    
    Bu servis şu özellikler sağlar:
    - DWG/DXF dosya okuma ve analiz
    - IFC BIM model işleme
    - 3D geometry conversion
    - Element extraction (duvarlar, kapılar, pencereler)
    - Format conversion between CAD types
    """
    
    def __init__(self):
        # self.geometry_utils = GeometryUtils()  # Will be initialized when available
        self.supported_formats = [CADFormat.DXF, CADFormat.IFC]
        
        # Add DWG support if ezdxf available
        if ezdxf:
            self.supported_formats.append(CADFormat.DWG)
            
        # Add 3D formats if open3d available
        if o3d:
            self.supported_formats.extend([CADFormat.PLY, CADFormat.OBJ, CADFormat.STL])

    async def process_cad_file(
        self,
        file_data: bytes,
        filename: str,
        target_format: Optional[CADFormat] = None
    ) -> ProcessingResult:
        """
        CAD dosyasını işle ve analiz et
        
        Args:
            file_data: Dosya binary verisi
            filename: Dosya adı
            target_format: Hedef format (conversion için)
            
        Returns:
            ProcessingResult: İşleme sonucu
            
        Raises:
            ProcessingError: Dosya işleme hatası
            ValidationError: Format desteği yok
        """
        
        start_time = datetime.now()
        file_id = str(uuid.uuid4())
        
        logger.info(
            "CAD file processing başladı",
            file_id=file_id,
            filename=filename,
            size_bytes=len(file_data)
        )
        
        try:
            # Detect file format
            detected_format = self._detect_format(filename, file_data)
            
            if detected_format not in self.supported_formats:
                raise ValueError(f"Desteklenmeyen format: {detected_format}")
            
            # Process based on format
            if detected_format == CADFormat.DXF:
                elements, metadata = await self._process_dxf_file(file_data)
            elif detected_format == CADFormat.IFC:
                elements, metadata = await self._process_ifc_file(file_data)
            elif detected_format in [CADFormat.PLY, CADFormat.OBJ, CADFormat.STL]:
                elements, metadata = await self._process_3d_file(file_data, detected_format)
            else:
                raise RuntimeError(f"Format handler not implemented: {detected_format}")
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            result = ProcessingResult(
                file_id=file_id,
                format=detected_format,
                elements=elements,
                metadata=metadata,
                processing_time_ms=processing_time
            )
            
            logger.info(
                "CAD file processing tamamlandı",
                file_id=file_id,
                element_count=len(elements),
                processing_time_ms=processing_time
            )
            
            return result
            
        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            logger.error(
                "CAD file processing hatası",
                file_id=file_id,
                filename=filename,
                error=str(e),
                processing_time_ms=processing_time,
                exc_info=True
            )
            raise RuntimeError(f"CAD file processing failed: {str(e)}")

    async def _process_dxf_file(self, file_data: bytes) -> Tuple[List[CADElement], Dict[str, Any]]:
        """DXF dosyası işle"""
        
        if not ezdxf:
            raise RuntimeError("ezdxf library not available")
        
        try:
            # Create temporary file for ezdxf
            with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            try:
                # Try to read DXF file
                doc = ezdxf.readfile(temp_path)
            except ezdxf.DXFStructureError:
                # Try recovery mode
                logger.warning("DXF structure error, attempting recovery")
                doc, auditor = recover.readfile(temp_path)
                
            # Extract metadata
            metadata = {
                "dxf_version": doc.dxfversion,
                "layer_count": len(doc.layers),
                "block_count": len(doc.blocks),
                "entity_count": len(list(doc.modelspace()))
            }
            
            # Extract elements
            elements = []
            
            # Process model space entities
            for entity in doc.modelspace():
                cad_element = self._convert_dxf_entity(entity)
                if cad_element:
                    elements.append(cad_element)
            
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
            return elements, metadata
            
        except Exception as e:
            logger.error("DXF processing error", error=str(e))
            raise RuntimeError(f"DXF processing failed: {str(e)}")

    async def _process_ifc_file(self, file_data: bytes) -> Tuple[List[CADElement], Dict[str, Any]]:
        """IFC dosyası işle"""
        
        if not ifcopenshell:
            raise RuntimeError("ifcopenshell library not available")
        
        try:
            # Create temporary file for ifcopenshell
            with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            # Read IFC file
            model = ifcopenshell.open(temp_path)
            
            # Extract metadata
            metadata = {
                "ifc_version": model.schema,
                "project_name": self._get_ifc_project_name(model),
                "building_count": len(model.by_type("IfcBuilding")),
                "space_count": len(model.by_type("IfcSpace")),
                "element_count": len(model.by_type("IfcBuildingElement"))
            }
            
            # Extract elements
            elements = []
            
            # Process walls
            for wall in model.by_type("IfcWall"):
                element = self._convert_ifc_wall(wall)
                if element:
                    elements.append(element)
            
            # Process doors
            for door in model.by_type("IfcDoor"):
                element = self._convert_ifc_door(door)
                if element:
                    elements.append(element)
            
            # Process windows
            for window in model.by_type("IfcWindow"):
                element = self._convert_ifc_window(window)
                if element:
                    elements.append(element)
            
            # Process spaces
            for space in model.by_type("IfcSpace"):
                element = self._convert_ifc_space(space)
                if element:
                    elements.append(element)
            
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
            return elements, metadata
            
        except Exception as e:
            logger.error("IFC processing error", error=str(e))
            raise RuntimeError(f"IFC processing failed: {str(e)}")

    async def _process_3d_file(
        self, 
        file_data: bytes, 
        format: CADFormat
    ) -> Tuple[List[CADElement], Dict[str, Any]]:
        """3D dosya formatlarını işle (PLY, OBJ, STL)"""
        
        if not o3d:
            raise RuntimeError("open3d library not available")
        
        try:
            # Create temporary file
            suffix = f'.{format.value}'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file.write(file_data)
                temp_path = temp_file.name
            
            # Read 3D mesh
            mesh = o3d.io.read_triangle_mesh(temp_path)
            
            if len(mesh.vertices) == 0:
                raise RuntimeError("No vertices found in 3D file")
            
            # Extract metadata
            metadata = {
                "vertex_count": len(mesh.vertices),
                "triangle_count": len(mesh.triangles),
                "has_normals": mesh.has_vertex_normals(),
                "has_colors": mesh.has_vertex_colors(),
                "bounding_box": self._get_mesh_bounds(mesh)
            }
            
            # Create single mesh element
            elements = [CADElement(
                id=str(uuid.uuid4()),
                type=ElementType.FURNITURE,  # Generic 3D object
                properties={
                    "format": format.value,
                    "vertex_count": len(mesh.vertices),
                    "triangle_count": len(mesh.triangles)
                },
                geometry={
                    "type": "mesh",
                    "bounds": metadata["bounding_box"]
                }
            )]
            
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
            
            return elements, metadata
            
        except Exception as e:
            logger.error("3D file processing error", error=str(e))
            raise RuntimeError(f"3D file processing failed: {str(e)}")

    def _detect_format(self, filename: str, file_data: bytes) -> CADFormat:
        """Dosya formatını tespit et"""
        
        # Check file extension first
        ext = Path(filename).suffix.lower()
        
        if ext == ".dwg":
            return CADFormat.DWG
        elif ext == ".dxf":
            return CADFormat.DXF
        elif ext == ".ifc":
            return CADFormat.IFC
        elif ext == ".ply":
            return CADFormat.PLY
        elif ext == ".obj":
            return CADFormat.OBJ
        elif ext == ".stl":
            return CADFormat.STL
        
        # Check file content for known signatures
        header = file_data[:100].lower()
        
        if b"autocad" in header or b"dxf" in header:
            return CADFormat.DXF
        elif b"iso-10303" in header or header.startswith(b"iso-"):
            return CADFormat.IFC
        elif header.startswith(b"ply"):
            return CADFormat.PLY
        elif b"solid" in header or header.startswith(b"solid"):
            return CADFormat.STL
        
        # Default fallback
        raise ValueError(f"Could not detect format for file: {filename}")

    def _convert_dxf_entity(self, entity) -> Optional[CADElement]:
        """DXF entity'yi CADElement'e çevir"""
        
        entity_type = entity.dxftype()
        element_id = str(uuid.uuid4())
        
        try:
            if entity_type == "LINE":
                return CADElement(
                    id=element_id,
                    type=ElementType.WALL,  # Assume lines are walls
                    layer=getattr(entity, 'layer', None),
                    properties={
                        "length": entity.dxf.start.distance(entity.dxf.end),
                        "color": getattr(entity.dxf, 'color', 0)
                    },
                    geometry={
                        "type": "line",
                        "start": {"x": entity.dxf.start.x, "y": entity.dxf.start.y},
                        "end": {"x": entity.dxf.end.x, "y": entity.dxf.end.y}
                    }
                )
                
            elif entity_type == "LWPOLYLINE":
                points = [(p[0], p[1]) for p in entity.get_points()]
                return CADElement(
                    id=element_id,
                    type=ElementType.WALL,
                    layer=getattr(entity, 'layer', None),
                    properties={
                        "point_count": len(points),
                        "closed": entity.closed
                    },
                    geometry={
                        "type": "polyline",
                        "points": [{"x": p[0], "y": p[1]} for p in points]
                    }
                )
                
            elif entity_type == "CIRCLE":
                return CADElement(
                    id=element_id,
                    type=ElementType.FURNITURE,
                    layer=getattr(entity, 'layer', None),
                    properties={
                        "radius": entity.dxf.radius,
                        "area": 3.14159 * entity.dxf.radius ** 2
                    },
                    geometry={
                        "type": "circle",
                        "center": {"x": entity.dxf.center.x, "y": entity.dxf.center.y},
                        "radius": entity.dxf.radius
                    }
                )
                
            elif entity_type == "TEXT" or entity_type == "MTEXT":
                return CADElement(
                    id=element_id,
                    type=ElementType.ANNOTATION,
                    layer=getattr(entity, 'layer', None),
                    properties={
                        "text": getattr(entity.dxf, 'text', ''),
                        "height": getattr(entity.dxf, 'height', 0)
                    },
                    geometry={
                        "type": "text",
                        "position": {"x": entity.dxf.insert.x, "y": entity.dxf.insert.y}
                    }
                )
                
        except Exception as e:
            logger.warning(f"Failed to convert DXF entity {entity_type}: {str(e)}")
            return None
        
        return None

    def _convert_ifc_wall(self, wall) -> Optional[CADElement]:
        """IFC duvarını CADElement'e çevir"""
        
        try:
            element_id = str(uuid.uuid4())
            
            # Get wall properties
            properties = {
                "name": getattr(wall, 'Name', '') or '',
                "tag": getattr(wall, 'Tag', '') or '',
                "predefined_type": getattr(wall, 'PredefinedType', '') or ''
            }
            
            # Try to get geometry
            geometry = {"type": "wall"}
            
            # Get wall type properties if available
            wall_type = getattr(wall, 'IsTypedBy', None)
            if wall_type and len(wall_type) > 0:
                type_obj = wall_type[0].RelatingType
                if hasattr(type_obj, 'HasPropertySets'):
                    # Extract properties from property sets
                    for prop_set in type_obj.HasPropertySets:
                        if hasattr(prop_set, 'HasProperties'):
                            for prop in prop_set.HasProperties:
                                if hasattr(prop, 'Name') and hasattr(prop, 'NominalValue'):
                                    properties[prop.Name] = str(prop.NominalValue)
            
            return CADElement(
                id=element_id,
                type=ElementType.WALL,
                properties=properties,
                geometry=geometry
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert IFC wall: {str(e)}")
            return None

    def _convert_ifc_door(self, door) -> Optional[CADElement]:
        """IFC kapıyı CADElement'e çevir"""
        
        try:
            element_id = str(uuid.uuid4())
            
            properties = {
                "name": getattr(door, 'Name', '') or '',
                "tag": getattr(door, 'Tag', '') or '',
                "predefined_type": getattr(door, 'PredefinedType', '') or ''
            }
            
            return CADElement(
                id=element_id,
                type=ElementType.DOOR,
                properties=properties,
                geometry={"type": "door"}
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert IFC door: {str(e)}")
            return None

    def _convert_ifc_window(self, window) -> Optional[CADElement]:
        """IFC pencereyi CADElement'e çevir"""
        
        try:
            element_id = str(uuid.uuid4())
            
            properties = {
                "name": getattr(window, 'Name', '') or '',
                "tag": getattr(window, 'Tag', '') or '',
                "predefined_type": getattr(window, 'PredefinedType', '') or ''
            }
            
            return CADElement(
                id=element_id,
                type=ElementType.WINDOW,
                properties=properties,
                geometry={"type": "window"}
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert IFC window: {str(e)}")
            return None

    def _convert_ifc_space(self, space) -> Optional[CADElement]:
        """IFC space'i CADElement'e çevir"""
        
        try:
            element_id = str(uuid.uuid4())
            
            properties = {
                "name": getattr(space, 'Name', '') or '',
                "long_name": getattr(space, 'LongName', '') or '',
                "description": getattr(space, 'Description', '') or ''
            }
            
            return CADElement(
                id=element_id,
                type=ElementType.ROOM,
                properties=properties,
                geometry={"type": "space"}
            )
            
        except Exception as e:
            logger.warning(f"Failed to convert IFC space: {str(e)}")
            return None

    def _get_ifc_project_name(self, model) -> str:
        """IFC proje adını al"""
        
        try:
            projects = model.by_type("IfcProject")
            if projects:
                return getattr(projects[0], 'Name', '') or 'Unnamed Project'
        except:
            pass
        
        return 'Unknown Project'

    def _get_mesh_bounds(self, mesh) -> Dict[str, float]:
        """3D mesh sınırlarını hesapla"""
        
        if o3d and len(mesh.vertices) > 0:
            vertices = np.asarray(mesh.vertices)
            
            return {
                "min_x": float(vertices[:, 0].min()),
                "max_x": float(vertices[:, 0].max()),
                "min_y": float(vertices[:, 1].min()),
                "max_y": float(vertices[:, 1].max()),
                "min_z": float(vertices[:, 2].min()),
                "max_z": float(vertices[:, 2].max()),
                "center_x": float(vertices[:, 0].mean()),
                "center_y": float(vertices[:, 1].mean()),
                "center_z": float(vertices[:, 2].mean())
            }
        
        return {}

    async def convert_layout_to_dxf(
        self,
        walls: List[Any],  # List[WallElement]
        doors: List[Any],  # List[DoorElement] 
        windows: List[Any]  # List[WindowElement]
    ) -> bytes:
        """Layout'u DXF formatına çevir"""
        
        if not ezdxf:
            raise RuntimeError("ezdxf library not available for DXF export")
        
        try:
            # Create new DXF document
            doc = ezdxf.new('R2010')  # Modern DXF version
            msp = doc.modelspace()
            
            # Create layers
            doc.layers.new(name='WALLS', dxfattribs={'color': 1})  # Red
            doc.layers.new(name='DOORS', dxfattribs={'color': 3})  # Green
            doc.layers.new(name='WINDOWS', dxfattribs={'color': 4})  # Cyan
            
            # Add walls
            for wall in walls:
                msp.add_line(
                    (wall.start.x, wall.start.y),
                    (wall.end.x, wall.end.y),
                    dxfattribs={'layer': 'WALLS'}
                )
            
            # Add doors (as blocks or simple representations)
            for door in doors:
                if door.wall_index < len(walls):
                    wall = walls[door.wall_index]
                    
                    # Calculate door position on wall
                    wall_vec = (wall.end.x - wall.start.x, wall.end.y - wall.start.y)
                    wall_length = (wall_vec[0]**2 + wall_vec[1]**2)**0.5
                    
                    if wall_length > 0:
                        unit_vec = (wall_vec[0]/wall_length, wall_vec[1]/wall_length)
                        door_pos = (
                            wall.start.x + unit_vec[0] * door.position,
                            wall.start.y + unit_vec[1] * door.position
                        )
                        
                        # Add door symbol (simple rectangle)
                        door_half = door.width / 2
                        perp_vec = (-unit_vec[1], unit_vec[0])  # Perpendicular vector
                        
                        door_p1 = (
                            door_pos[0] - unit_vec[0] * door_half,
                            door_pos[1] - unit_vec[1] * door_half
                        )
                        door_p2 = (
                            door_pos[0] + unit_vec[0] * door_half,
                            door_pos[1] + unit_vec[1] * door_half
                        )
                        
                        msp.add_line(door_p1, door_p2, dxfattribs={'layer': 'DOORS'})
            
            # Add windows (similar to doors)
            for window in windows:
                if window.wall_index < len(walls):
                    wall = walls[window.wall_index]
                    
                    # Calculate window position
                    wall_vec = (wall.end.x - wall.start.x, wall.end.y - wall.start.y)
                    wall_length = (wall_vec[0]**2 + wall_vec[1]**2)**0.5
                    
                    if wall_length > 0:
                        unit_vec = (wall_vec[0]/wall_length, wall_vec[1]/wall_length)
                        window_pos = (
                            wall.start.x + unit_vec[0] * window.position,
                            wall.start.y + unit_vec[1] * window.position
                        )
                        
                        # Add window symbol
                        window_half = window.width / 2
                        
                        window_p1 = (
                            window_pos[0] - unit_vec[0] * window_half,
                            window_pos[1] - unit_vec[1] * window_half
                        )
                        window_p2 = (
                            window_pos[0] + unit_vec[0] * window_half,
                            window_pos[1] + unit_vec[1] * window_half
                        )
                        
                        msp.add_line(window_p1, window_p2, dxfattribs={'layer': 'WINDOWS'})
            
            # Save to memory
            with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as temp_file:
                doc.saveas(temp_file.name)
                
                # Read back as bytes
                with open(temp_file.name, 'rb') as f:
                    dxf_data = f.read()
                
                # Clean up
                Path(temp_file.name).unlink(missing_ok=True)
            
            logger.info(
                "Layout DXF export başarılı",
                wall_count=len(walls),
                door_count=len(doors),
                window_count=len(windows)
            )
            
            return dxf_data
            
        except Exception as e:
            logger.error("DXF export hatası", error=str(e))
            raise RuntimeError(f"DXF export failed: {str(e)}")

    def get_supported_formats(self) -> List[CADFormat]:
        """Desteklenen formatları döndür"""
        return self.supported_formats.copy()

    async def analyze_existing_project(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Existing project analysis for AI recommendations
        
        Args:
            file_data: CAD file binary data
            filename: File name
            
        Returns:
            Dict: Analysis results for AI processing
        """
        
        logger.info("Existing project analysis başlatıldı", filename=filename)
        
        try:
            # Process the CAD file
            result = await self.process_cad_file(file_data, filename)
            
            # Analyze elements for improvements
            analysis = {
                "file_info": {
                    "format": result.format.value,
                    "element_count": len(result.elements),
                    "processing_time": result.processing_time_ms
                },
                "element_statistics": self._analyze_element_statistics(result.elements),
                "spatial_analysis": self._analyze_spatial_relationships(result.elements),
                "compliance_issues": self._detect_compliance_issues(result.elements),
                "improvement_suggestions": self._generate_improvement_suggestions(result.elements)
            }
            
            logger.info(
                "Existing project analysis tamamlandı",
                filename=filename,
                issue_count=len(analysis["compliance_issues"])
            )
            
            return analysis
            
        except Exception as e:
            logger.error("Project analysis hatası", filename=filename, error=str(e))
            raise RuntimeError(f"Project analysis failed: {str(e)}")

    def _analyze_element_statistics(self, elements: List[CADElement]) -> Dict[str, Any]:
        """Element istatistikleri analizi"""
        
        stats = {}
        
        # Count by type
        type_counts = {}
        for element in elements:
            element_type = element.type.value
            type_counts[element_type] = type_counts.get(element_type, 0) + 1
        
        stats["element_counts"] = type_counts
        stats["total_elements"] = len(elements)
        
        # Analyze walls
        walls = [e for e in elements if e.type == ElementType.WALL]
        if walls:
            wall_lengths = []
            for wall in walls:
                if wall.geometry.get("type") == "line":
                    start = wall.geometry["start"]
                    end = wall.geometry["end"]
                    length = ((end["x"] - start["x"])**2 + (end["y"] - start["y"])**2)**0.5
                    wall_lengths.append(length)
            
            if wall_lengths:
                stats["wall_analysis"] = {
                    "count": len(walls),
                    "total_length": sum(wall_lengths),
                    "avg_length": sum(wall_lengths) / len(wall_lengths),
                    "min_length": min(wall_lengths),
                    "max_length": max(wall_lengths)
                }
        
        return stats

    def _analyze_spatial_relationships(self, elements: List[CADElement]) -> Dict[str, Any]:
        """Spatial relationships analizi"""
        
        # Basic spatial analysis
        relationships = {
            "rooms_without_doors": 0,
            "isolated_elements": 0,
            "overlapping_elements": 0
        }
        
        # TODO: Implement detailed spatial analysis
        # This would require geometric intersection testing
        
        return relationships

    def _detect_compliance_issues(self, elements: List[CADElement]) -> List[Dict[str, Any]]:
        """Compliance issues detection"""
        
        issues = []
        
        # Check for missing doors
        rooms = [e for e in elements if e.type == ElementType.ROOM]
        doors = [e for e in elements if e.type == ElementType.DOOR]
        
        if len(rooms) > 0 and len(doors) == 0:
            issues.append({
                "type": "missing_doors",
                "severity": "error",
                "message": "Odalar tespit edildi ancak kapı bulunamadı",
                "suggestion": "Her odaya erişim kapısı ekleyin"
            })
        
        # Check for accessibility issues
        if len(doors) > 0:
            narrow_doors = []
            for door in doors:
                door_width = door.properties.get("width", 0)
                if door_width > 0 and door_width < 800:  # 80cm minimum
                    narrow_doors.append(door)
            
            if narrow_doors:
                issues.append({
                    "type": "narrow_doors",
                    "severity": "warning", 
                    "message": f"{len(narrow_doors)} kapı engelli erişim için dar",
                    "suggestion": "Kapı genişliklerini minimum 80cm yapın"
                })
        
        return issues

    def _generate_improvement_suggestions(self, elements: List[CADElement]) -> List[Dict[str, Any]]:
        """Improvement suggestions generation"""
        
        suggestions = []
        
        walls = [e for e in elements if e.type == ElementType.WALL]
        doors = [e for e in elements if e.type == ElementType.DOOR]
        windows = [e for e in elements if e.type == ElementType.WINDOW]
        
        # Suggest adding missing elements
        if len(walls) > 0 and len(doors) == 0:
            suggestions.append({
                "type": "add_doors",
                "priority": "high",
                "description": "Kapı elemanları ekleyin",
                "impact": "Fonksiyonel erişim sağlar"
            })
        
        if len(walls) > 0 and len(windows) == 0:
            suggestions.append({
                "type": "add_windows",
                "priority": "medium",
                "description": "Doğal ışık için pencere ekleyin",
                "impact": "Yaşam kalitesi artar"
            })
        
        # Suggest layout optimization
        if len(elements) > 20:
            suggestions.append({
                "type": "simplify_layout",
                "priority": "low",
                "description": "Layout'u basitleştirin",
                "impact": "Daha okunabilir tasarım"
            })
        
        return suggestions