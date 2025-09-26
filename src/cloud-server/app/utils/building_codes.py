"""
Turkish Building Code Validator for ArchBuilder.AI

Validates architectural layouts against Turkish Building Code regulations.
Implements specific requirements for residential and commercial buildings.

Author: ArchBuilder.AI Team
Date: 2025-09-26
"""

from typing import Dict, List, Any, Tuple
from enum import Enum

from structlog import get_logger

from ..schemas.layout_schemas import (
    LayoutData, ValidationError, 
    WallElement, DoorElement, WindowElement, RoomBoundary
)

logger = get_logger(__name__)


class BuildingType(str, Enum):
    """Bina tipleri"""
    RESIDENTIAL = "konut"
    COMMERCIAL = "ticari"
    OFFICE = "ofis"
    EDUCATIONAL = "eğitim"
    HEALTHCARE = "sağlık"
    INDUSTRIAL = "endüstriyel"


class RoomFunction(str, Enum):
    """Oda fonksiyonları - yönetmelik kategorileri"""
    LIVING = "yaşama"  # Salon, oturma odası
    SLEEPING = "uyku"  # Yatak odası
    COOKING = "pişirme"  # Mutfak
    SANITARY = "hijyen"  # Banyo, WC
    STORAGE = "depolama"  # Depo, kiler
    CIRCULATION = "sirkülasyon"  # Koridor, merdiven
    TECHNICAL = "teknik"  # Kazan dairesi, elektrik odası


class TurkishBuildingCodeValidator:
    """
    Türk Yapı Yönetmeliği validator sınıfı
    
    Referanslar:
    - Planlı Alanlar İmar Yönetmeliği
    - Yapı Denetim Uygulama Usul ve Esasları
    - Engelsiz Yaşam Mevzuatı
    - Yangın Güvenlik Yönetmeliği
    """
    
    def __init__(self):
        # Minimum alan gereksinimleri (m²)
        self.min_room_areas = {
            RoomFunction.LIVING: 12.0,
            RoomFunction.SLEEPING: 9.0,
            RoomFunction.COOKING: 6.0,
            RoomFunction.SANITARY: 2.4,
            RoomFunction.STORAGE: 2.0,
        }
        
        # Minimum genişlik gereksinimleri (mm)
        self.min_room_widths = {
            RoomFunction.LIVING: 2700,
            RoomFunction.SLEEPING: 2400,
            RoomFunction.COOKING: 1800,
            RoomFunction.SANITARY: 1200,
            RoomFunction.CIRCULATION: 1000,
        }
        
        # Minimum tavan yüksekliği (mm)
        self.min_ceiling_heights = {
            RoomFunction.LIVING: 2500,
            RoomFunction.SLEEPING: 2500,
            RoomFunction.COOKING: 2400,
            RoomFunction.SANITARY: 2200,
            RoomFunction.STORAGE: 2200,
        }
        
        # Kapı genişlik gereksinimleri (mm)
        self.door_widths = {
            "main_entrance": {"min": 900, "max": 1200},
            "interior": {"min": 700, "max": 1000},
            "bathroom": {"min": 600, "max": 800},
            "fire_exit": {"min": 800, "max": 1200},
        }
        
        # Doğal aydınlatma oranları (pencere alanı / yer alanı)
        self.natural_light_ratios = {
            RoomFunction.LIVING: 1/8,    # 1/8
            RoomFunction.SLEEPING: 1/8,   # 1/8
            RoomFunction.COOKING: 1/10,   # 1/10
            RoomFunction.SANITARY: 1/12,  # 1/12 (veya mekanik havalandırma)
        }

    async def validate_layout(self, layout: LayoutData) -> Dict[str, List[ValidationError]]:
        """
        Layout'u Türk Yapı Yönetmeliği'ne göre doğrula
        
        Args:
            layout: Doğrulanacak layout data
            
        Returns:
            Dict: errors ve warnings listeleri
        """
        
        logger.info("Türk Yapı Yönetmeliği validation başlatıldı")
        
        errors = []
        warnings = []
        
        try:
            # 1. Oda minimum alanları
            room_errors, room_warnings = await self._validate_room_areas(layout)
            errors.extend(room_errors)
            warnings.extend(room_warnings)
            
            # 2. Kapı gereksinimleri
            door_errors, door_warnings = await self._validate_door_requirements(layout)
            errors.extend(door_errors)
            warnings.extend(door_warnings)
            
            # 3. Doğal aydınlatma
            light_errors, light_warnings = await self._validate_natural_lighting(layout)
            errors.extend(light_errors)
            warnings.extend(light_warnings)
            
            # 4. Yangın güvenliği
            fire_errors, fire_warnings = await self._validate_fire_safety(layout)
            errors.extend(fire_errors)
            warnings.extend(fire_warnings)
            
            # 5. Engelli erişimi
            access_errors, access_warnings = await self._validate_accessibility_compliance(layout)
            errors.extend(access_errors)
            warnings.extend(access_warnings)
            
            # 6. Havalandırma gereksinimleri
            ventilation_errors, ventilation_warnings = await self._validate_ventilation(layout)
            errors.extend(ventilation_errors)
            warnings.extend(ventilation_warnings)
            
            logger.info(
                "Yapı yönetmeliği validation tamamlandı",
                error_count=len(errors),
                warning_count=len(warnings)
            )
            
            return {"errors": errors, "warnings": warnings}
            
        except Exception as e:
            logger.error("Yapı yönetmeliği validation hatası", error=str(e))
            return {
                "errors": [ValidationError(
                    code="BUILDING_CODE_VALIDATION_FAILED",
                    message=f"Yapı yönetmeliği doğrulama hatası: {str(e)}",
                    severity="critical",
                    location="Genel",
                    suggestion="Sistem yöneticisine başvurun"
                )],
                "warnings": []
            }

    async def _validate_room_areas(self, layout: LayoutData) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Oda minimum alanları kontrol et"""
        
        errors = []
        warnings = []
        
        for room in layout.rooms:
            room_function = self._classify_room_function(room.name)
            
            if room_function in self.min_room_areas:
                min_area = self.min_room_areas[room_function]
                
                if room.area < min_area:
                    errors.append(ValidationError(
                        code="ROOM_AREA_BELOW_MINIMUM",
                        message=f"Oda '{room.name}' alanı yetersiz: {room.area:.1f}m² (minimum {min_area}m²)",
                        severity="error",
                        location=room.name,
                        suggestion=f"Oda alanını en az {min_area}m² yapın - Yapı Yönetmeliği Madde 12"
                    ))
                elif room.area < min_area * 1.1:  # 10% tolerance for warning
                    warnings.append(ValidationError(
                        code="ROOM_AREA_MARGINAL",
                        message=f"Oda '{room.name}' alanı minimum değere yakın: {room.area:.1f}m²",
                        severity="warning",
                        location=room.name,
                        suggestion="Daha konforlu kullanım için alanı artırın"
                    ))
        
        # Toplam yaşama alanı kontrolü (konut için)
        living_rooms = [room for room in layout.rooms 
                       if self._classify_room_function(room.name) == RoomFunction.LIVING]
        sleeping_rooms = [room for room in layout.rooms 
                         if self._classify_room_function(room.name) == RoomFunction.SLEEPING]
        
        total_living_area = sum(room.area for room in living_rooms)
        total_sleeping_area = sum(room.area for room in sleeping_rooms)
        
        # Konut için minimum toplam yaşama alanı (salon + yatak odaları)
        min_total_living = 16.0  # Tek kişilik konut için
        bedroom_count = len(sleeping_rooms)
        if bedroom_count > 1:
            min_total_living += (bedroom_count - 1) * 9.0  # Her ek yatak odası için
        
        actual_total = total_living_area + total_sleeping_area
        if actual_total < min_total_living:
            errors.append(ValidationError(
                code="TOTAL_LIVING_AREA_INSUFFICIENT",
                message=f"Toplam yaşama alanı yetersiz: {actual_total:.1f}m² (minimum {min_total_living:.1f}m²)",
                severity="error",
                location="Genel yaşam alanları",
                suggestion="Salon ve yatak odası alanlarını artırın - Konut Yönetmeliği"
            ))
        
        return errors, warnings

    async def _validate_door_requirements(self, layout: LayoutData) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Kapı gereksinimleri kontrol et"""
        
        errors = []
        warnings = []
        
        # Ana giriş kapısı kontrolü
        main_entrance_doors = []
        for i, door in enumerate(layout.doors):
            if door.wall_index < len(layout.walls):
                wall = layout.walls[door.wall_index]
                if wall.type == "exterior":
                    main_entrance_doors.append((i, door))
        
        if not main_entrance_doors:
            errors.append(ValidationError(
                code="NO_MAIN_ENTRANCE",
                message="Ana giriş kapısı bulunamadı",
                severity="critical",
                location="Ana giriş",
                suggestion="Dış duvara ana giriş kapısı ekleyin"
            ))
        else:
            # Ana giriş kapısı boyut kontrolü
            for i, door in main_entrance_doors:
                min_width = self.door_widths["main_entrance"]["min"]
                max_width = self.door_widths["main_entrance"]["max"]
                
                if door.width < min_width:
                    errors.append(ValidationError(
                        code="MAIN_ENTRANCE_TOO_NARROW",
                        message=f"Ana giriş kapısı dar: {door.width}mm (minimum {min_width}mm)",
                        severity="error",
                        location=f"Kapı {i+1}",
                        suggestion="Ana giriş kapısını genişletin - Yapı Yönetmeliği Madde 15"
                    ))
                elif door.width > max_width:
                    warnings.append(ValidationError(
                        code="MAIN_ENTRANCE_VERY_WIDE",
                        message=f"Ana giriş kapısı çok geniş: {door.width}mm (maksimum {max_width}mm)",
                        severity="warning",
                        location=f"Kapı {i+1}",
                        suggestion="Kapı genişliğini standart ölçülere getirin"
                    ))
        
        # İç kapılar kontrolü
        for i, door in enumerate(layout.doors):
            if door.wall_index < len(layout.walls):
                wall = layout.walls[door.wall_index]
                if wall.type == "interior":
                    # Kapının hangi odaya ait olduğunu belirle
                    room_type = self._determine_door_room_type(door, layout)
                    
                    if room_type == "bathroom":
                        min_width = self.door_widths["bathroom"]["min"]
                        if door.width < min_width:
                            errors.append(ValidationError(
                                code="BATHROOM_DOOR_TOO_NARROW",
                                message=f"Banyo kapısı dar: {door.width}mm (minimum {min_width}mm)",
                                severity="error",
                                location=f"Kapı {i+1}",
                                suggestion="Banyo kapısını genişletin"
                            ))
                    else:
                        min_width = self.door_widths["interior"]["min"]
                        if door.width < min_width:
                            errors.append(ValidationError(
                                code="INTERIOR_DOOR_TOO_NARROW", 
                                message=f"İç kapı dar: {door.width}mm (minimum {min_width}mm)",
                                severity="error",
                                location=f"Kapı {i+1}"
                            ))
        
        # Kapı eşik yüksekliği (engelli erişim)
        for i, door in enumerate(layout.doors):
            if hasattr(door, 'threshold_height') and door.threshold_height > 20:
                warnings.append(ValidationError(
                    code="DOOR_THRESHOLD_HIGH",
                    message=f"Kapı eşiği yüksek: {door.threshold_height}mm (maksimum 20mm)",
                    severity="warning",
                    location=f"Kapı {i+1}",
                    suggestion="Engelli erişim için eşiği alçaltın"
                ))
        
        return errors, warnings

    async def _validate_natural_lighting(self, layout: LayoutData) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Doğal aydınlatma gereksinimleri"""
        
        errors = []
        warnings = []
        
        # Her oda için pencere alanı / yer alanı oranını kontrol et
        for room in layout.rooms:
            room_function = self._classify_room_function(room.name)
            
            if room_function in self.natural_light_ratios:
                required_ratio = self.natural_light_ratios[room_function]
                
                # Odanın pencerelerini bul
                room_window_area = self._calculate_room_window_area(room, layout)
                actual_ratio = room_window_area / (room.area * 1_000_000) if room.area > 0 else 0  # Convert m² to mm²
                
                if actual_ratio < required_ratio:
                    shortage_pct = (required_ratio - actual_ratio) / required_ratio * 100
                    
                    if shortage_pct > 50:  # Büyük eksiklik
                        errors.append(ValidationError(
                            code="INSUFFICIENT_NATURAL_LIGHT",
                            message=f"Oda '{room.name}' doğal aydınlatma yetersiz: {actual_ratio:.3f} (minimum {required_ratio:.3f})",
                            severity="error",
                            location=room.name,
                            suggestion="Pencere alanını artırın - Yapı Yönetmeliği Madde 18"
                        ))
                    else:  # Küçük eksiklik
                        warnings.append(ValidationError(
                            code="MARGINAL_NATURAL_LIGHT",
                            message=f"Oda '{room.name}' doğal aydınlatma sınırda: {actual_ratio:.3f}",
                            severity="warning",
                            location=room.name
                        ))
                
        return errors, warnings

    async def _validate_fire_safety(self, layout: LayoutData) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Yangın güvenliği gereksinimleri"""
        
        errors = []
        warnings = []
        
        # Yangın çıkışı kontrolü
        fire_exit_doors = []
        for i, door in enumerate(layout.doors):
            if door.wall_index < len(layout.walls):
                wall = layout.walls[door.wall_index]
                if wall.type == "exterior" and door.width >= self.door_widths["fire_exit"]["min"]:
                    fire_exit_doors.append((i, door))
        
        if len(fire_exit_doors) == 0:
            errors.append(ValidationError(
                code="NO_FIRE_EXIT",
                message="Yangın çıkışı yok - minimum 80cm genişlikte dış kapı gerekli",
                severity="critical",
                suggestion="Yangın güvenlik yönetmeliği için dış kapı ekleyin"
            ))
        
        # Kaçış yolu genişliği
        corridors = self._identify_escape_routes(layout)
        for corridor in corridors:
            min_width = 1200  # mm - yangın güvenlik yönetmeliği
            if corridor.get("width", 0) < min_width:
                errors.append(ValidationError(
                    code="ESCAPE_ROUTE_TOO_NARROW",
                    message=f"Kaçış yolu dar: {corridor.get('width', 0):.0f}mm (minimum {min_width}mm)",
                    severity="error",
                    suggestion="Yangın güvenliği için koridor genişletilmeli"
                ))
        
        # Ölü çıkış kontrolü (dead-end corridors)
        dead_ends = self._find_dead_end_spaces(layout)
        if dead_ends:
            for dead_end in dead_ends:
                warnings.append(ValidationError(
                    code="DEAD_END_SPACE",
                    message=f"Ölü çıkış alanı tespit edildi: {dead_end}",
                    severity="warning",
                    suggestion="Alternatif çıkış yolu düşünün"
                ))
        
        return errors, warnings

    async def _validate_accessibility_compliance(self, layout: LayoutData) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Engelli erişim uyumluluğu"""
        
        errors = []
        warnings = []
        
        # Tekerlekli sandalye erişim genişlikleri
        wheelchair_min_door = 850  # mm
        wheelchair_min_corridor = 1200  # mm
        
        # Ana giriş erişimi
        main_doors = [door for i, door in enumerate(layout.doors) 
                     if door.wall_index < len(layout.walls) and 
                     layout.walls[door.wall_index].type == "exterior"]
        
        accessible_entrance = any(door.width >= wheelchair_min_door for door in main_doors)
        
        if not accessible_entrance:
            warnings.append(ValidationError(
                code="NO_ACCESSIBLE_ENTRANCE",
                message=f"Engelli erişim için uygun giriş yok (minimum {wheelchair_min_door}mm)",
                severity="warning",
                suggestion="Engelsiz Yaşam Mevzuatı için giriş genişletilmeli"
            ))
        
        # İç mekan erişimi
        narrow_doors = [i for i, door in enumerate(layout.doors) 
                       if door.width < wheelchair_min_door]
        
        if narrow_doors:
            warnings.append(ValidationError(
                code="NARROW_INTERIOR_DOORS",
                message=f"{len(narrow_doors)} kapı engelli erişim için dar",
                severity="warning",
                suggestion="Kapı genişliklerini 85cm'e çıkarın"
            ))
        
        # WC erişimi (eğer varsa)
        wc_rooms = [room for room in layout.rooms 
                   if "wc" in room.name.lower() or "banyo" in room.name.lower()]
        
        for wc in wc_rooms:
            if wc.area < 4.5:  # Engelli WC için minimum alan
                warnings.append(ValidationError(
                    code="WC_TOO_SMALL_FOR_WHEELCHAIR",
                    message=f"WC '{wc.name}' engelli erişim için küçük: {wc.area:.1f}m² (minimum 4.5m²)",
                    severity="warning",
                    location=wc.name
                ))
        
        return errors, warnings

    async def _validate_ventilation(self, layout: LayoutData) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Havalandırma gereksinimleri"""
        
        errors = []
        warnings = []
        
        # Mutfak havalandırması
        kitchens = [room for room in layout.rooms 
                   if self._classify_room_function(room.name) == RoomFunction.COOKING]
        
        for kitchen in kitchens:
            kitchen_windows = self._calculate_room_window_area(kitchen, layout)
            if kitchen_windows == 0:
                warnings.append(ValidationError(
                    code="KITCHEN_NO_NATURAL_VENTILATION",
                    message=f"Mutfak '{kitchen.name}' doğal havalandırma yok",
                    severity="warning",
                    location=kitchen.name,
                    suggestion="Pencere ekleyin veya mekanik havalandırma planlayın"
                ))
        
        # Banyo havalandırması
        bathrooms = [room for room in layout.rooms 
                    if self._classify_room_function(room.name) == RoomFunction.SANITARY]
        
        for bathroom in bathrooms:
            bathroom_windows = self._calculate_room_window_area(bathroom, layout)
            if bathroom_windows == 0 and bathroom.area > 3.0:  # Büyük banyolar için
                warnings.append(ValidationError(
                    code="BATHROOM_NO_VENTILATION",
                    message=f"Banyo '{bathroom.name}' havalandırma yetersiz",
                    severity="warning",
                    location=bathroom.name,
                    suggestion="Pencere veya aspiratör düşünülmeli"
                ))
        
        return errors, warnings

    def _classify_room_function(self, room_name: str) -> RoomFunction:
        """Oda adından fonksiyonu belirle"""
        
        name_lower = room_name.lower()
        
        if any(keyword in name_lower for keyword in ["salon", "oturma", "living"]):
            return RoomFunction.LIVING
        elif any(keyword in name_lower for keyword in ["yatak", "uyku", "bedroom"]):
            return RoomFunction.SLEEPING
        elif any(keyword in name_lower for keyword in ["mutfak", "kitchen"]):
            return RoomFunction.COOKING
        elif any(keyword in name_lower for keyword in ["banyo", "wc", "tuvalet", "bathroom"]):
            return RoomFunction.SANITARY
        elif any(keyword in name_lower for keyword in ["depo", "kiler", "storage"]):
            return RoomFunction.STORAGE
        elif any(keyword in name_lower for keyword in ["koridor", "hole", "corridor"]):
            return RoomFunction.CIRCULATION
        else:
            return RoomFunction.LIVING  # Default to living space

    def _determine_door_room_type(self, door: DoorElement, layout: LayoutData) -> str:
        """Kapının hangi tip odaya ait olduğunu belirle"""
        
        # Basitleştirilmiş implementasyon
        # Gerçek implementasyonda geometric analysis gerekli
        
        # For now, assume bathroom doors are smaller
        if door.width <= 700:
            return "bathroom"
        else:
            return "general"

    def _calculate_room_window_area(self, room: RoomBoundary, layout: LayoutData) -> float:
        """Odanın toplam pencere alanını hesapla (mm²)"""
        
        total_area = 0.0
        
        # Basitleştirilmiş - room boundaries'e bakarak pencere bul
        for window in layout.windows:
            if window.wall_index in getattr(room, 'boundaries', []):
                window_area = window.width * window.height
                total_area += window_area
        
        return total_area

    def _identify_escape_routes(self, layout: LayoutData) -> List[Dict[str, Any]]:
        """Kaçış yollarını tespit et"""
        
        # Basitleştirilmiş implementasyon
        # Gerçekte geometric analysis ile corridor detection gerekli
        
        escape_routes = []
        
        corridors = [room for room in layout.rooms 
                    if self._classify_room_function(room.name) == RoomFunction.CIRCULATION]
        
        for corridor in corridors:
            # Estimate corridor width from area
            estimated_width = (corridor.area * 1000) ** 0.5 * 1000  # Rough estimation in mm
            escape_routes.append({
                "name": corridor.name,
                "width": estimated_width,
                "area": corridor.area
            })
        
        return escape_routes

    def _find_dead_end_spaces(self, layout: LayoutData) -> List[str]:
        """Ölü çıkış alanlarını bul"""
        
        # Basitleştirilmiş implementasyon
        # Gerçek implementasyon connectivity analysis gerektirir
        
        dead_ends = []
        
        # Tek kapısı olan odaları tespit et
        room_door_count = {}
        for room in layout.rooms:
            room_door_count[room.name] = 0
        
        for door in layout.doors:
            # Bu basitleştirilmiş - gerçekte geometric analysis gerekir
            for room in layout.rooms:
                if door.wall_index in getattr(room, 'boundaries', []):
                    room_door_count[room.name] += 1
        
        # Tek kapısı olan ve büyük olan odalar (>6m²) dead-end riski taşır
        for room_name, door_count in room_door_count.items():
            room = next((r for r in layout.rooms if r.name == room_name), None)
            if room and door_count <= 1 and room.area > 6.0:
                dead_ends.append(room_name)
        
        return dead_ends