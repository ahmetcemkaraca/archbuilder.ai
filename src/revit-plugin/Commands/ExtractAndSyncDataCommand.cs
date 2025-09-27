using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Autodesk.Revit.ApplicationServices;
using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.DependencyInjection;
using ArchBuilder.Desktop.Models;
using ArchBuilder.Desktop.Interfaces;

namespace ArchBuilder.RevitPlugin.Commands
{
    /// <summary>
    /// Revit verilerini çıkarıp lokal/bulut depolamaya kaydetme komutu
    /// </summary>
    [Transaction(TransactionMode.ReadOnly)]
    [Regeneration(RegenerationOption.Manual)]
    public class ExtractAndSyncDataCommand : IExternalCommand
    {
        private readonly ILogger<ExtractAndSyncDataCommand> _logger;
        private readonly ILocalDataManager _localDataManager;
        private readonly ICloudStorageManager _cloudStorageManager;

        public ExtractAndSyncDataCommand()
        {
            // DI container'dan service'leri al
            var serviceProvider = RevitPluginApplication.ServiceProvider;
            _logger = serviceProvider.GetRequiredService<ILogger<ExtractAndSyncDataCommand>>();
            _localDataManager = serviceProvider.GetRequiredService<ILocalDataManager>();
            _cloudStorageManager = serviceProvider.GetRequiredService<ICloudStorageManager>();
        }

        /// <summary>
        /// Komut çalıştırma
        /// </summary>
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                var uiDoc = commandData.Application.ActiveUIDocument;
                var doc = uiDoc.Document;

                _logger.LogInformation("Revit veri çıkarma başladı", new { ProjectName = doc.Title });

                // Revit verilerini çıkar
                var modelData = ExtractRevitData(doc);

                // Async işlemleri Task.Run ile çalıştır
                Task.Run(async () => await ProcessDataAsync(modelData));

                // Kullanıcıya başarı mesajı göster
                TaskDialog.Show("ArchBuilder.AI", 
                    "Revit verileri başarıyla çıkarıldı ve işlem arka planda devam ediyor.\n\n" +
                    "Lokal kayıt tamamlandığında bildirim alacaksınız.");

                return Result.Succeeded;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Revit veri çıkarma hatası");
                message = $"Veri çıkarma hatası: {ex.Message}";
                return Result.Failed;
            }
        }

        /// <summary>
        /// Revit document'inden veri çıkar
        /// </summary>
        private RevitModelData ExtractRevitData(Document doc)
        {
            var modelData = new RevitModelData
            {
                ProjectName = doc.Title,
                RevitVersion = doc.Application.VersionNumber,
                DocumentTitle = doc.ProjectInformation?.Name ?? doc.Title,
                ExtractedAt = DateTime.UtcNow
            };

            // Model metadata'sını çıkar
            modelData.Metadata = ExtractModelMetadata(doc);

            // Model bounds hesapla
            modelData.ModelBounds = CalculateModelBounds(doc);

            // Duvarları çıkar
            modelData.Walls = ExtractWalls(doc);
            
            // Kapıları çıkar
            modelData.Doors = ExtractDoors(doc);
            
            // Pencereleri çıkar
            modelData.Windows = ExtractWindows(doc);
            
            // Odaları çıkar
            modelData.Rooms = ExtractRooms(doc);
            
            // Döşemeleri çıkar
            modelData.Floors = ExtractFloors(doc);
            
            // Çatıları çıkar
            modelData.Roofs = ExtractRoofs(doc);

            _logger.LogInformation("Revit veri çıkarma tamamlandı",
                new { 
                    WallCount = modelData.Walls.Count,
                    DoorCount = modelData.Doors.Count,
                    WindowCount = modelData.Windows.Count,
                    RoomCount = modelData.Rooms.Count,
                    FloorCount = modelData.Floors.Count,
                    RoofCount = modelData.Roofs.Count
                });

            return modelData;
        }

        /// <summary>
        /// Veri işleme (lokal kayıt + bulut sync)
        /// </summary>
        private async Task ProcessDataAsync(RevitModelData modelData)
        {
            try
            {
                // 1. Lokal JSON kayıt
                var localResult = await _localDataManager.SaveRevitDataAsync(modelData);
                
                if (!localResult.Success)
                {
                    _logger.LogError("Lokal veri kayıt hatası", new { Error = localResult.Message });
                    return;
                }

                _logger.LogInformation("Lokal veri kaydı tamamlandı",
                    new { CorrelationId = localResult.CorrelationId, FilePath = localResult.FilePath });

                // 2. Kullanıcı izni kontrol et
                if (!await _cloudStorageManager.HasUserPermissionAsync())
                {
                    _logger.LogInformation("Bulut sync izni yok, sadece lokal kayıt yapıldı");
                    return;
                }

                // 3. Bulut sync
                var syncOptions = new SyncOptions
                {
                    CompressBeforeUpload = true,
                    VerifyIntegrity = true,
                    DeleteLocalAfterUpload = false, // Lokal kopyayı koru
                    CreateBackup = true,
                    Tags = new Dictionary<string, string>
                    {
                        ["project"] = modelData.ProjectName,
                        ["revit-version"] = modelData.RevitVersion,
                        ["extracted-at"] = modelData.ExtractedAt.ToString("O")
                    }
                };

                var syncResult = await _cloudStorageManager.SyncToCloudAsync(localResult.FilePath, syncOptions);

                if (syncResult.Success)
                {
                    _logger.LogInformation("Bulut sync tamamlandı",
                        new { 
                            CorrelationId = syncResult.CorrelationId,
                            RemotePath = syncResult.RemotePath,
                            Duration = syncResult.Duration.TotalSeconds
                        });

                    // Başarı bildirimi göster
                    ShowNotification("Bulut Sync Tamamlandı", 
                        $"Proje verileri başarıyla bulut depolamaya yüklendi.\n\n" +
                        $"Süre: {syncResult.Duration.TotalSeconds:F1} saniye\n" +
                        $"Boyut: {syncResult.SizeBytes / 1024:N0} KB");
                }
                else
                {
                    _logger.LogError("Bulut sync hatası", new { Error = syncResult.Message });
                    
                    ShowNotification("Bulut Sync Hatası", 
                        $"Veriler lokal olarak kaydedildi ancak bulut sync başarısız.\n\n" +
                        $"Hata: {syncResult.Message}");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Veri işleme genel hatası");
                
                ShowNotification("Veri İşleme Hatası", 
                    $"Beklenmeyen bir hata oluştu: {ex.Message}");
            }
        }

        #region Data Extraction Methods

        private ModelMetadata ExtractModelMetadata(Document doc)
        {
            var metadata = new ModelMetadata
            {
                Author = doc.ProjectInformation?.Author ?? "Bilinmiyor",
                LastSaved = doc.ProjectInformation?.LastSavedBy != null ? DateTime.UtcNow : DateTime.MinValue,
                Units = doc.DisplayUnitSystem.ToString()
            };

            // Element sayıları
            var elementCounts = new Dictionary<string, int>();
            
            // Kategorilere göre element sayıları
            var categories = new[]
            {
                BuiltInCategory.OST_Walls,
                BuiltInCategory.OST_Doors, 
                BuiltInCategory.OST_Windows,
                BuiltInCategory.OST_Rooms,
                BuiltInCategory.OST_Floors,
                BuiltInCategory.OST_Roofs
            };

            foreach (var category in categories)
            {
                var count = new FilteredElementCollector(doc)
                    .OfCategory(category)
                    .WhereElementIsNotElementType()
                    .Count();
                
                elementCounts[category.ToString()] = count;
                metadata.TotalElements += count;
            }

            metadata.ElementCounts = elementCounts;

            // Proje bilgileri
            if (doc.ProjectInformation != null)
            {
                metadata.ProjectInfo = new Dictionary<string, object>
                {
                    ["Name"] = doc.ProjectInformation.Name ?? "",
                    ["Number"] = doc.ProjectInformation.Number ?? "",
                    ["Address"] = doc.ProjectInformation.Address ?? "",
                    ["BuildingName"] = doc.ProjectInformation.BuildingName ?? ""
                };
            }

            return metadata;
        }

        private BoundingBox3D CalculateModelBounds(Document doc)
        {
            var bounds = new BoundingBox3D();
            
            try
            {
                // Optimized collector - sadece geometrik elementler
                var collector = new FilteredElementCollector(doc)
                    .WhereElementIsNotElementType()
                    .Where(e => e.Category != null && 
                               e.get_BoundingBox(null) != null &&
                               IsModelElement(e.Category.Id));

                var allElements = collector.ToList();

                if (allElements.Any())
                {
                    var minX = double.MaxValue;
                    var minY = double.MaxValue;
                    var minZ = double.MaxValue;
                    var maxX = double.MinValue;
                    var maxY = double.MinValue;
                    var maxZ = double.MinValue;

                    var processedCount = 0;
                    foreach (var element in allElements)
                    {
                        var bbox = element.get_BoundingBox(null);
                        if (bbox != null && 
                            IsValidBoundingBox(bbox))
                        {
                            minX = Math.Min(minX, bbox.Min.X);
                            minY = Math.Min(minY, bbox.Min.Y);
                            minZ = Math.Min(minZ, bbox.Min.Z);
                            maxX = Math.Max(maxX, bbox.Max.X);
                            maxY = Math.Max(maxY, bbox.Max.Y);
                            maxZ = Math.Max(maxZ, bbox.Max.Z);
                            processedCount++;
                        }
                    }

                    if (processedCount > 0)
                    {
                        bounds.Min = new Point3D(minX, minY, minZ);
                        bounds.Max = new Point3D(maxX, maxY, maxZ);
                        
                        _logger.LogDebug("Model bounds hesaplandı",
                            new { ProcessedElements = processedCount, TotalElements = allElements.Count });
                    }
                    else
                    {
                        _logger.LogWarning("Geçerli bounding box bulunamadı, varsayılan bounds kullanılıyor");
                        bounds.Min = new Point3D(0, 0, 0);
                        bounds.Max = new Point3D(100, 100, 100);
                    }
                }
                else
                {
                    _logger.LogWarning("Model bounds için element bulunamadı");
                    bounds.Min = new Point3D(0, 0, 0);
                    bounds.Max = new Point3D(0, 0, 0);
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Model bounds hesaplama hatası");
                
                // Fallback bounds
                bounds.Min = new Point3D(0, 0, 0);
                bounds.Max = new Point3D(100, 100, 100);
            }

            return bounds;
        }

        /// <summary>
        /// Model bounds hesaplaması için geçerli category kontrolü
        /// </summary>
        private bool IsModelElement(ElementId categoryId)
        {
            if (categoryId == null || categoryId == ElementId.InvalidElementId) return false;
            
            var builtInCategoryId = categoryId.IntegerValue;

            return builtInCategoryId == (int)BuiltInCategory.OST_Walls ||
                   builtInCategoryId == (int)BuiltInCategory.OST_Floors ||
                   builtInCategoryId == (int)BuiltInCategory.OST_Roofs ||
                   builtInCategoryId == (int)BuiltInCategory.OST_Columns ||
                   builtInCategoryId == (int)BuiltInCategory.OST_StructuralFraming ||
                   builtInCategoryId == (int)BuiltInCategory.OST_Windows ||
                   builtInCategoryId == (int)BuiltInCategory.OST_Doors;
        }

        /// <summary>
        /// BoundingBox geçerlilik kontrolü
        /// </summary>
        private bool IsValidBoundingBox(BoundingBox bbox)
        {
            if (bbox?.Min == null || bbox?.Max == null) return false;
            
            // Çok küçük veya çok büyük bounding box'ları filtrele
            var width = Math.Abs(bbox.Max.X - bbox.Min.X);
            var height = Math.Abs(bbox.Max.Y - bbox.Min.Y);
            var depth = Math.Abs(bbox.Max.Z - bbox.Min.Z);
            
            const double minSize = 0.001; // 1mm
            const double maxSize = 10000; // 10km
            
            return width > minSize && height > minSize && depth > minSize &&
                   width < maxSize && height < maxSize && depth < maxSize;
        }

        private List<WallData> ExtractWalls(Document doc)
        {
            var walls = new List<WallData>();

            var wallCollector = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Walls)
                .WhereElementIsNotElementType();

            foreach (Wall wall in wallCollector)
            {
                try
                {
                    var locationCurve = wall.Location as LocationCurve;
                    if (locationCurve?.Curve != null)
                    {
                        var curve = locationCurve.Curve;
                        Point3D startPoint, endPoint;

                        // Curve tipine göre start/end point belirle
                        if (curve is Line line)
                        {
                            startPoint = new Point3D(line.GetEndPoint(0).X, line.GetEndPoint(0).Y, line.GetEndPoint(0).Z);
                            endPoint = new Point3D(line.GetEndPoint(1).X, line.GetEndPoint(1).Y, line.GetEndPoint(1).Z);
                        }
                        else if (curve is Arc arc)
                        {
                            startPoint = new Point3D(arc.GetEndPoint(0).X, arc.GetEndPoint(0).Y, arc.GetEndPoint(0).Z);
                            endPoint = new Point3D(arc.GetEndPoint(1).X, arc.GetEndPoint(1).Y, arc.GetEndPoint(1).Z);
                        }
                        else
                        {
                            // Diğer curve tipleri için genel approach
                            startPoint = new Point3D(curve.GetEndPoint(0).X, curve.GetEndPoint(0).Y, curve.GetEndPoint(0).Z);
                            endPoint = new Point3D(curve.GetEndPoint(1).X, curve.GetEndPoint(1).Y, curve.GetEndPoint(1).Z);
                        }

                        var wallData = new WallData
                        {
                            Id = wall.Id.ToString(),
                            Name = wall.Name ?? "İsimsiz Duvar",
                            StartPoint = startPoint,
                            EndPoint = endPoint,
                            Height = GetWallHeight(wall),
                            Thickness = wall.Width,
                            WallType = wall.WallType?.Name ?? "Bilinmiyor",
                            Level = doc.GetElement(wall.LevelId)?.Name ?? "Bilinmiyor"
                        };

                        // Ek duvar özelliklerini çıkar
                        ExtractWallProperties(wall, wallData);

                        // Parametreleri çıkar
                        ExtractElementParameters(wall, wallData.Parameters);

                        walls.Add(wallData);
                    }
                    else
                    {
                        _logger.LogDebug("Wall location curve bulunamadı", new { WallId = wall.Id });
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Duvar veri çıkarma hatası", new { WallId = wall.Id });
                }
            }

            return walls;
        }

        /// <summary>
        /// Duvar yüksekliğini güvenli şekilde al
        /// </summary>
        private double GetWallHeight(Wall wall)
        {
            try
            {
                // Önce user height parametresini dene
                var userHeightParam = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM);
                if (userHeightParam?.HasValue == true)
                {
                    return userHeightParam.AsDouble();
                }

                // Sonra unconnected height'ı dene
                var unconnectedHeightParam = wall.get_Parameter(BuiltInParameter.WALL_ATTR_WIDTH_PARAM);
                if (unconnectedHeightParam?.HasValue == true)
                {
                    return unconnectedHeightParam.AsDouble();
                }

                // Son çare: bounding box'tan hesapla
                var bbox = wall.get_BoundingBox(null);
                if (bbox != null)
                {
                    return Math.Abs(bbox.Max.Z - bbox.Min.Z);
                }

                return 0;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Wall height hesaplama hatası", new { WallId = wall.Id });
                return 0;
            }
        }

        /// <summary>
        /// Ek duvar özelliklerini çıkar
        /// </summary>
        private void ExtractWallProperties(Wall wall, WallData wallData)
        {
            try
            {
                // Structural kullanım
                wallData.IsStructural = wall.get_Parameter(BuiltInParameter.WALL_STRUCTURAL_SIGNIFICANT)?.AsInteger() == 1;

                // Room bounding
                wallData.IsRoomBounding = wall.get_Parameter(BuiltInParameter.WALL_ATTR_ROOM_BOUNDING)?.AsInteger() == 1;

                // Wall function
                var wallFunction = wall.WallType?.Function;
                if (wallFunction.HasValue)
                {
                    wallData.WallFunction = wallFunction.Value.ToString();
                }
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Wall properties çıkarma hatası", new { WallId = wall.Id });
            }
        }

        private List<DoorData> ExtractDoors(Document doc)
        {
            var doors = new List<DoorData>();

            var doorCollector = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Doors)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>();

            foreach (var door in doorCollector)
            {
                try
                {
                    if (door.Location is LocationPoint location)
                    {
                        var doorData = new DoorData
                        {
                            Id = door.Id.ToString(),
                            Name = door.Name ?? "İsimsiz Kapı",
                            Location = new Point3D(location.Point.X, location.Point.Y, location.Point.Z),
                            HostWallId = door.Host?.Id.ToString() ?? "",
                            Width = GetFamilyParameterValue(door, BuiltInParameter.DOOR_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM),
                            Height = GetFamilyParameterValue(door, BuiltInParameter.DOOR_HEIGHT, BuiltInParameter.FAMILY_HEIGHT_PARAM),
                            DoorType = door.Symbol?.Name ?? "Bilinmiyor",
                            Rotation = location.Rotation
                        };

                        // Host wall bilgilerini kontrol et
                        if (door.Host is Wall hostWall)
                        {
                            doorData.HostWallId = hostWall.Id.ToString();
                        }

                        // Parametreleri çıkar
                        ExtractElementParameters(door, doorData.Parameters);

                        doors.Add(doorData);
                    }
                    else
                    {
                        _logger.LogDebug("Door location point bulunamadı", new { DoorId = door.Id });
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Kapı veri çıkarma hatası", new { DoorId = door.Id });
                }
            }

            return doors;
        }

        private List<WindowData> ExtractWindows(Document doc)
        {
            var windows = new List<WindowData>();

            var windowCollector = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Windows)
                .WhereElementIsNotElementType()
                .Cast<FamilyInstance>();

            foreach (var window in windowCollector)
            {
                try
                {
                    if (window.Location is LocationPoint location)
                    {
                        var windowData = new WindowData
                        {
                            Id = window.Id.ToString(),
                            Name = window.Name ?? "İsimsiz Pencere",
                            Location = new Point3D(location.Point.X, location.Point.Y, location.Point.Z),
                            HostWallId = window.Host?.Id.ToString() ?? "",
                            Width = GetFamilyParameterValue(window, BuiltInParameter.WINDOW_WIDTH, BuiltInParameter.FAMILY_WIDTH_PARAM),
                            Height = GetFamilyParameterValue(window, BuiltInParameter.WINDOW_HEIGHT, BuiltInParameter.FAMILY_HEIGHT_PARAM),
                            WindowType = window.Symbol?.Name ?? "Bilinmiyor",
                            SillHeight = GetParameterValue(window, BuiltInParameter.INSTANCE_SILL_HEIGHT_PARAM)
                        };

                        // Host wall bilgilerini kontrol et
                        if (window.Host is Wall hostWall)
                        {
                            windowData.HostWallId = hostWall.Id.ToString();
                        }

                        // Parametreleri çıkar
                        ExtractElementParameters(window, windowData.Parameters);

                        windows.Add(windowData);
                    }
                    else
                    {
                        _logger.LogDebug("Window location point bulunamadı", new { WindowId = window.Id });
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Pencere veri çıkarma hatası", new { WindowId = window.Id });
                }
            }

            return windows;
        }

        /// <summary>
        /// Family instance parametresi değerini güvenli şekilde al
        /// </summary>
        private double GetFamilyParameterValue(FamilyInstance familyInstance, params BuiltInParameter[] parameterOptions)
        {
            foreach (var paramOption in parameterOptions)
            {
                try
                {
                    // Önce instance parametresini dene
                    var instanceParam = familyInstance.get_Parameter(paramOption);
                    if (instanceParam?.HasValue == true)
                    {
                        return instanceParam.AsDouble();
                    }

                    // Sonra symbol parametresini dene
                    var symbolParam = familyInstance.Symbol?.get_Parameter(paramOption);
                    if (symbolParam?.HasValue == true)
                    {
                        return symbolParam.AsDouble();
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogDebug(ex, "Family parameter okuma hatası", 
                        new { FamilyInstanceId = familyInstance.Id, Parameter = paramOption });
                }
            }

            return 0;
        }

        /// <summary>
        /// Element parametresi değerini güvenli şekilde al
        /// </summary>
        private double GetParameterValue(Element element, BuiltInParameter parameter)
        {
            try
            {
                var param = element.get_Parameter(parameter);
                return param?.HasValue == true ? param.AsDouble() : 0;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Parameter değer okuma hatası", 
                    new { ElementId = element.Id, Parameter = parameter });
                return 0;
            }
        }

        private List<RoomData> ExtractRooms(Document doc)
        {
            var rooms = new List<RoomData>();

            var roomCollector = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Rooms)
                .WhereElementIsNotElementType();

            foreach (Room room in roomCollector)
            {
                try
                {
                    // Room geçerli kontrolü
                    if (room.Area <= 0 || room.Location == null)
                    {
                        _logger.LogDebug("Geçersiz room atlandı", new { RoomId = room.Id, Area = room.Area });
                        continue;
                    }

                    if (room.Location is LocationPoint location)
                    {
                        var roomData = new RoomData
                        {
                            Id = room.Id.ToString(),
                            Name = room.Name ?? "İsimsiz Oda",
                            Number = room.Number ?? "0",
                            Location = new Point3D(location.Point.X, location.Point.Y, location.Point.Z),
                            Area = room.Area,
                            Volume = room.Volume,
                            Level = room.Level?.Name ?? "Bilinmiyor"
                        };

                        // Room boundary'sini çıkar - doğru API kullanımı
                        try
                        {
                            var boundaryOptions = new SpatialElementBoundaryOptions
                            {
                                SpatialElementBoundaryLocation = SpatialElementBoundaryLocation.Finish,
                                StoreFreeBoundaryFaces = false
                            };

                            var boundaries = room.GetBoundarySegments(boundaryOptions);
                            
                            if (boundaries != null && boundaries.Count > 0)
                            {
                                // İlk boundary loop'unu al (outer boundary)
                                var outerBoundary = boundaries[0];
                                foreach (BoundarySegment segment in outerBoundary)
                                {
                                    var curve = segment.GetCurve();
                                    if (curve != null)
                                    {
                                        roomData.Boundary.Add(new Point3D(
                                            curve.GetEndPoint(0).X, 
                                            curve.GetEndPoint(0).Y, 
                                            curve.GetEndPoint(0).Z));
                                    }
                                }
                            }
                        }
                        catch (Exception boundaryEx)
                        {
                            _logger.LogWarning(boundaryEx, "Room boundary çıkarma hatası", new { RoomId = room.Id });
                            
                            // Fallback: Room location'dan basit boundary oluştur
                            var radius = Math.Sqrt(room.Area / Math.PI); // Yaklaşık radius
                            var center = location.Point;
                            
                            // 8 noktalı octagon oluştur
                            for (int i = 0; i < 8; i++)
                            {
                                var angle = i * Math.PI / 4;
                                var x = center.X + radius * Math.Cos(angle);
                                var y = center.Y + radius * Math.Sin(angle);
                                roomData.Boundary.Add(new Point3D(x, y, center.Z));
                            }
                        }

                        // Parametreleri çıkar
                        ExtractElementParameters(room, roomData.Parameters);

                        rooms.Add(roomData);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Oda veri çıkarma hatası", new { RoomId = room.Id });
                }
            }

            return rooms;
        }

        private List<FloorData> ExtractFloors(Document doc)
        {
            var floors = new List<FloorData>();

            var floorCollector = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Floors)
                .WhereElementIsNotElementType();

            foreach (Floor floor in floorCollector)
            {
                try
                {
                    var floorData = new FloorData
                    {
                        Id = floor.Id.ToString(),
                        Name = floor.Name,
                        FloorType = floor.FloorType?.Name ?? "Bilinmiyor",
                        Level = doc.GetElement(floor.LevelId)?.Name ?? "Bilinmiyor",
                        Thickness = floor.get_Parameter(BuiltInParameter.FLOOR_ATTR_THICKNESS_PARAM)?.AsDouble() ?? 0,
                        Area = floor.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() ?? 0
                    };

                    // Floor outline'ını çıkar - modern API kullanarak
                    try
                    {
                        var sketchId = floor.SketchId;
                        if (sketchId != ElementId.InvalidElementId)
                        {
                            var sketch = doc.GetElement(sketchId) as Sketch;
                            if (sketch != null)
                            {
                                var sketchElements = sketch.GetAllElements();
                                foreach (ElementId elemId in sketchElements)
                                {
                                    var sketchElement = doc.GetElement(elemId);
                                    if (sketchElement is ModelCurve modelCurve)
                                    {
                                        var curve = modelCurve.GeometryCurve;
                                        if (curve != null)
                                        {
                                            floorData.Outline.Add(new Point3D(
                                                curve.GetEndPoint(0).X, 
                                                curve.GetEndPoint(0).Y, 
                                                curve.GetEndPoint(0).Z));
                                        }
                                    }
                                }
                            }
                        }
                    }
                    catch (Exception sketchEx)
                    {
                        _logger.LogWarning(sketchEx, "Floor sketch çıkarma hatası", new { FloorId = floor.Id });
                        
                        // Fallback: BoundingBox kullan
                        var bbox = floor.get_BoundingBox(null);
                        if (bbox != null)
                        {
                            floorData.Outline.Add(new Point3D(bbox.Min.X, bbox.Min.Y, bbox.Min.Z));
                            floorData.Outline.Add(new Point3D(bbox.Max.X, bbox.Min.Y, bbox.Min.Z));
                            floorData.Outline.Add(new Point3D(bbox.Max.X, bbox.Max.Y, bbox.Min.Z));
                            floorData.Outline.Add(new Point3D(bbox.Min.X, bbox.Max.Y, bbox.Min.Z));
                        }
                    }

                    // Parametreleri çıkar
                    ExtractElementParameters(floor, floorData.Parameters);

                    floors.Add(floorData);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Döşeme veri çıkarma hatası", new { FloorId = floor.Id });
                }
            }

            return floors;
        }

        private List<RoofData> ExtractRoofs(Document doc)
        {
            var roofs = new List<RoofData>();

            var roofCollector = new FilteredElementCollector(doc)
                .OfCategory(BuiltInCategory.OST_Roofs)
                .WhereElementIsNotElementType();

            foreach (RoofBase roof in roofCollector)
            {
                try
                {
                    var roofData = new RoofData
                    {
                        Id = roof.Id.ToString(),
                        Name = roof.Name,
                        RoofType = roof.RoofType?.Name ?? "Bilinmiyor",
                        Area = roof.get_Parameter(BuiltInParameter.HOST_AREA_COMPUTED)?.AsDouble() ?? 0
                    };

                    // Roof outline'ını çıkar (basitleştirilmiş)
                    var bbox = roof.get_BoundingBox(null);
                    if (bbox != null)
                    {
                        roofData.Outline.Add(new Point3D(bbox.Min.X, bbox.Min.Y, bbox.Min.Z));
                        roofData.Outline.Add(new Point3D(bbox.Max.X, bbox.Min.Y, bbox.Min.Z));
                        roofData.Outline.Add(new Point3D(bbox.Max.X, bbox.Max.Y, bbox.Min.Z));
                        roofData.Outline.Add(new Point3D(bbox.Min.X, bbox.Max.Y, bbox.Min.Z));
                    }

                    // Parametreleri çıkar
                    ExtractElementParameters(roof, roofData.Parameters);

                    roofs.Add(roofData);
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Çatı veri çıkarma hatası", new { RoofId = roof.Id });
                }
            }

            return roofs;
        }

        private void ExtractElementParameters(Element element, Dictionary<string, object> parameters)
        {
            try
            {
                foreach (Parameter param in element.Parameters)
                {
                    if (param?.Definition?.Name != null && 
                        !string.IsNullOrWhiteSpace(param.Definition.Name))
                    {
                        try
                        {
                            // Parameter read-only kontrolü
                            if (!param.IsReadOnly)
                            {
                                object value = ExtractParameterValue(param);
                                if (value != null)
                                {
                                    // Parametre adını temizle (invalid karakterleri kaldır)
                                    var cleanName = SanitizeParameterName(param.Definition.Name);
                                    parameters[cleanName] = value;
                                }
                            }
                        }
                        catch (Exception paramEx)
                        {
                            _logger.LogDebug(paramEx, "Tek parametre çıkarma hatası", 
                                new { ElementId = element.Id, ParameterName = param.Definition.Name });
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Parameter çıkarma genel hatası", new { ElementId = element.Id });
            }
        }

        /// <summary>
        /// Parameter değerini güvenli şekilde çıkar
        /// </summary>
        private object ExtractParameterValue(Parameter param)
        {
            try
            {
                // Önce HasValue kontrolü ama fallback ile
                if (param.HasValue)
                {
                    return param.StorageType switch
                    {
                        StorageType.Double => param.AsDouble(),
                        StorageType.Integer => param.AsInteger(),
                        StorageType.String => param.AsString() ?? "",
                        StorageType.ElementId => param.AsElementId()?.ToString() ?? "",
                        _ => param.AsValueString() ?? ""
                    };
                }
                
                // HasValue false olsa bile value string deneyelim
                var valueString = param.AsValueString();
                return !string.IsNullOrEmpty(valueString) ? valueString : null;
            }
            catch (Autodesk.Revit.Exceptions.InvalidOperationException)
            {
                // Parameter değeri okunamıyor, null döndür
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Parameter değer çıkarma hatası", 
                    new { ParameterName = param.Definition?.Name });
                return null;
            }
        }

        /// <summary>
        /// Parametre adını JSON için temizle
        /// </summary>
        private string SanitizeParameterName(string parameterName)
        {
            if (string.IsNullOrWhiteSpace(parameterName)) return "UnknownParameter";
            
            // JSON property name için problematik karakterleri temizle
            return parameterName
                .Replace("\"", "'")
                .Replace("\n", " ")
                .Replace("\r", " ")
                .Replace("\t", " ")
                .Replace("\\", "/")
                .Trim();
        }

        #endregion

        #region UI Helpers

        private void ShowNotification(string title, string message)
        {
            try
            {
                // Revit UI thread'de TaskDialog göster
                TaskDialog.Show(title, message);
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Notification gösterme hatası");
            }
        }

        #endregion
    }
}