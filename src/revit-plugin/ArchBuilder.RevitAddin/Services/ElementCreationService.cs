using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Service for creating Revit elements with validation and error handling
    /// </summary>
    public class ElementCreationService : IElementCreationService
    {
        private readonly ILogger<ElementCreationService> _logger;
        private readonly ITransactionService _transactionService;
        private readonly IValidationService _validationService;

        public ElementCreationService(
            ILogger<ElementCreationService> logger,
            ITransactionService transactionService,
            IValidationService validationService)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _transactionService = transactionService ?? throw new ArgumentNullException(nameof(transactionService));
            _validationService = validationService ?? throw new ArgumentNullException(nameof(validationService));
        }

        /// <summary>
        /// Create walls from wall definitions
        /// </summary>
        public List<Wall> CreateWalls(Document document, List<WallDefinition> wallDefinitions, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (wallDefinitions == null || !wallDefinitions.Any())
                throw new ArgumentException("Wall definitions cannot be null or empty", nameof(wallDefinitions));

            using var scope = _logger.BeginScope("CreateWalls {CorrelationId}", correlationId);

            var createdWalls = new List<Wall>();

            try
            {
                _logger.LogInformation("Creating {WallCount} walls", wallDefinitions.Count);

                var result = _transactionService.ExecuteTransaction(document, "Create Walls", transaction =>
                {
                    foreach (var wallDef in wallDefinitions)
                    {
                        try
                        {
                            // Validate wall type
                            if (!ValidateWallType(document, wallDef.WallTypeName))
                            {
                                _logger.LogWarning("Wall type not found: {WallTypeName}, using default", wallDef.WallTypeName);
                                wallDef.WallTypeName = GetDefaultWallType(document);
                            }

                            // Get or create level
                            var level = GetOrCreateLevel(document, wallDef.LevelName);

                            // Get wall type
                            var wallType = GetWallType(document, wallDef.WallTypeName);
                            if (wallType == null)
                            {
                                _logger.LogError("Failed to get wall type: {WallTypeName}", wallDef.WallTypeName);
                                continue;
                            }

                            // Create wall curve
                            var line = Line.CreateBound(wallDef.StartPoint, wallDef.EndPoint);
                            
                            // Create wall
                            var wall = Wall.Create(document, line, wallType.Id, level.Id, wallDef.Height, 0, false, false);
                            
                            if (wall != null)
                            {
                                // Set parameters
                                SetElementParameters(wall, wallDef.Parameters);
                                
                                createdWalls.Add(wall);
                                _logger.LogDebug("Created wall {WallId} from {StartPoint} to {EndPoint}", 
                                    wall.Id, wallDef.StartPoint, wallDef.EndPoint);
                            }
                            else
                            {
                                _logger.LogError("Failed to create wall from {StartPoint} to {EndPoint}", 
                                    wallDef.StartPoint, wallDef.EndPoint);
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "Error creating wall from {StartPoint} to {EndPoint}", 
                                wallDef.StartPoint, wallDef.EndPoint);
                        }
                    }
                }, correlationId);

                if (result)
                {
                    _logger.LogInformation("Successfully created {CreatedCount} walls", createdWalls.Count);
                }
                else
                {
                    _logger.LogError("Failed to create walls in transaction");
                }

                return createdWalls;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error creating walls");
                return createdWalls;
            }
        }

        /// <summary>
        /// Create doors from door definitions
        /// </summary>
        public List<FamilyInstance> CreateDoors(Document document, List<DoorDefinition> doorDefinitions, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (doorDefinitions == null || !doorDefinitions.Any())
                throw new ArgumentException("Door definitions cannot be null or empty", nameof(doorDefinitions));

            using var scope = _logger.BeginScope("CreateDoors {CorrelationId}", correlationId);

            var createdDoors = new List<FamilyInstance>();

            try
            {
                _logger.LogInformation("Creating {DoorCount} doors", doorDefinitions.Count);

                var result = _transactionService.ExecuteTransaction(document, "Create Doors", transaction =>
                {
                    foreach (var doorDef in doorDefinitions)
                    {
                        try
                        {
                            // Find host wall
                            var hostWall = FindElementById<Wall>(document, doorDef.HostWallId);
                            if (hostWall == null)
                            {
                                _logger.LogWarning("Host wall not found for door: {HostWallId}", doorDef.HostWallId);
                                continue;
                            }

                            // Validate door family
                            if (!ValidateDoorFamily(document, doorDef.FamilyName, doorDef.TypeName))
                            {
                                _logger.LogWarning("Door family/type not found: {FamilyName}/{TypeName}, using default", 
                                    doorDef.FamilyName, doorDef.TypeName);
                                var defaultDoor = GetDefaultDoorFamily(document);
                                doorDef.FamilyName = defaultDoor.familyName;
                                doorDef.TypeName = defaultDoor.typeName;
                            }

                            // Get door family and type
                            var doorFamily = GetFamily(document, doorDef.FamilyName);
                            var doorType = GetFamilyType(document, doorDef.FamilyName, doorDef.TypeName);
                            
                            if (doorFamily == null || doorType == null)
                            {
                                _logger.LogError("Failed to get door family/type: {FamilyName}/{TypeName}", 
                                    doorDef.FamilyName, doorDef.TypeName);
                                continue;
                            }

                            // Calculate position along wall
                            var wallCurve = (hostWall.Location as LocationCurve)?.Curve;
                            if (wallCurve == null)
                            {
                                _logger.LogError("Host wall has no curve for door placement");
                                continue;
                            }

                            var position = wallCurve.Evaluate(doorDef.PositionRatio);
                            var wallDirection = wallCurve.Direction;
                            var wallNormal = wallDirection.CrossProduct(XYZ.BasisZ).Normalize();

                            // Create door
                            var door = document.Create.NewFamilyInstance(
                                position, doorType, hostWall, StructuralType.NonStructural);

                            if (door != null)
                            {
                                // Set door parameters
                                SetElementParameters(door, doorDef.Parameters);
                                
                                // Set flip parameters
                                if (doorDef.FlipHand)
                                    door.flipHand();
                                if (doorDef.FlipFacing)
                                    door.flipFacing();

                                createdDoors.Add(door);
                                _logger.LogDebug("Created door {DoorId} at position {Position}", door.Id, position);
                            }
                            else
                            {
                                _logger.LogError("Failed to create door at position {Position}", position);
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "Error creating door for host wall {HostWallId}", doorDef.HostWallId);
                        }
                    }
                }, correlationId);

                if (result)
                {
                    _logger.LogInformation("Successfully created {CreatedCount} doors", createdDoors.Count);
                }
                else
                {
                    _logger.LogError("Failed to create doors in transaction");
                }

                return createdDoors;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error creating doors");
                return createdDoors;
            }
        }

        /// <summary>
        /// Create windows from window definitions
        /// </summary>
        public List<FamilyInstance> CreateWindows(Document document, List<WindowDefinition> windowDefinitions, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (windowDefinitions == null || !windowDefinitions.Any())
                throw new ArgumentException("Window definitions cannot be null or empty", nameof(windowDefinitions));

            using var scope = _logger.BeginScope("CreateWindows {CorrelationId}", correlationId);

            var createdWindows = new List<FamilyInstance>();

            try
            {
                _logger.LogInformation("Creating {WindowCount} windows", windowDefinitions.Count);

                var result = _transactionService.ExecuteTransaction(document, "Create Windows", transaction =>
                {
                    foreach (var windowDef in windowDefinitions)
                    {
                        try
                        {
                            // Find host wall
                            var hostWall = FindElementById<Wall>(document, windowDef.HostWallId);
                            if (hostWall == null)
                            {
                                _logger.LogWarning("Host wall not found for window: {HostWallId}", windowDef.HostWallId);
                                continue;
                            }

                            // Validate window family
                            if (!ValidateWindowFamily(document, windowDef.FamilyName, windowDef.TypeName))
                            {
                                _logger.LogWarning("Window family/type not found: {FamilyName}/{TypeName}, using default", 
                                    windowDef.FamilyName, windowDef.TypeName);
                                var defaultWindow = GetDefaultWindowFamily(document);
                                windowDef.FamilyName = defaultWindow.familyName;
                                windowDef.TypeName = defaultWindow.typeName;
                            }

                            // Get window family and type
                            var windowFamily = GetFamily(document, windowDef.FamilyName);
                            var windowType = GetFamilyType(document, windowDef.FamilyName, windowDef.TypeName);
                            
                            if (windowFamily == null || windowType == null)
                            {
                                _logger.LogError("Failed to get window family/type: {FamilyName}/{TypeName}", 
                                    windowDef.FamilyName, windowDef.TypeName);
                                continue;
                            }

                            // Calculate position along wall
                            var wallCurve = (hostWall.Location as LocationCurve)?.Curve;
                            if (wallCurve == null)
                            {
                                _logger.LogError("Host wall has no curve for window placement");
                                continue;
                            }

                            var position = wallCurve.Evaluate(windowDef.PositionRatio);
                            var wallDirection = wallCurve.Direction;
                            var wallNormal = wallDirection.CrossProduct(XYZ.BasisZ).Normalize();

                            // Adjust position for sill height
                            position = position + XYZ.BasisZ * windowDef.SillHeight;

                            // Create window
                            var window = document.Create.NewFamilyInstance(
                                position, windowType, hostWall, StructuralType.NonStructural);

                            if (window != null)
                            {
                                // Set window parameters
                                SetElementParameters(window, windowDef.Parameters);

                                createdWindows.Add(window);
                                _logger.LogDebug("Created window {WindowId} at position {Position}", window.Id, position);
                            }
                            else
                            {
                                _logger.LogError("Failed to create window at position {Position}", position);
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "Error creating window for host wall {HostWallId}", windowDef.HostWallId);
                        }
                    }
                }, correlationId);

                if (result)
                {
                    _logger.LogInformation("Successfully created {CreatedCount} windows", createdWindows.Count);
                }
                else
                {
                    _logger.LogError("Failed to create windows in transaction");
                }

                return createdWindows;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error creating windows");
                return createdWindows;
            }
        }

        /// <summary>
        /// Create rooms from room definitions
        /// </summary>
        public List<Room> CreateRooms(Document document, List<RoomDefinition> roomDefinitions, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (roomDefinitions == null || !roomDefinitions.Any())
                throw new ArgumentException("Room definitions cannot be null or empty", nameof(roomDefinitions));

            using var scope = _logger.BeginScope("CreateRooms {CorrelationId}", correlationId);

            var createdRooms = new List<Room>();

            try
            {
                _logger.LogInformation("Creating {RoomCount} rooms", roomDefinitions.Count);

                var result = _transactionService.ExecuteTransaction(document, "Create Rooms", transaction =>
                {
                    foreach (var roomDef in roomDefinitions)
                    {
                        try
                        {
                            // Get or create level
                            var level = GetOrCreateLevel(document, roomDef.LevelName);

                            // Create room boundary
                            if (roomDef.BoundaryPoints.Count < 3)
                            {
                                _logger.LogWarning("Room {RoomName} has insufficient boundary points", roomDef.Name);
                                continue;
                            }

                            // Create room
                            var room = document.Create.NewRoom(level, new UV(roomDef.BoundaryPoints[0].X, roomDef.BoundaryPoints[0].Y));
                            
                            if (room != null)
                            {
                                // Set room parameters
                                if (!string.IsNullOrEmpty(roomDef.Name))
                                {
                                    room.get_Parameter(BuiltInParameter.ROOM_NAME).Set(roomDef.Name);
                                }
                                if (!string.IsNullOrEmpty(roomDef.Number))
                                {
                                    room.get_Parameter(BuiltInParameter.ROOM_NUMBER).Set(roomDef.Number);
                                }

                                SetElementParameters(room, roomDef.Parameters);

                                createdRooms.Add(room);
                                _logger.LogDebug("Created room {RoomId} with name {RoomName}", room.Id, roomDef.Name);
                            }
                            else
                            {
                                _logger.LogError("Failed to create room {RoomName}", roomDef.Name);
                            }
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "Error creating room {RoomName}", roomDef.Name);
                        }
                    }
                }, correlationId);

                if (result)
                {
                    _logger.LogInformation("Successfully created {CreatedCount} rooms", createdRooms.Count);
                }
                else
                {
                    _logger.LogError("Failed to create rooms in transaction");
                }

                return createdRooms;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error creating rooms");
                return createdRooms;
            }
        }

        /// <summary>
        /// Validate wall type exists in document
        /// </summary>
        public bool ValidateWallType(Document document, string wallTypeName)
        {
            if (document == null || string.IsNullOrEmpty(wallTypeName))
                return false;

            try
            {
                var wallType = GetWallType(document, wallTypeName);
                return wallType != null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating wall type: {WallTypeName}", wallTypeName);
                return false;
            }
        }

        /// <summary>
        /// Validate door family exists in document
        /// </summary>
        public bool ValidateDoorFamily(Document document, string familyName, string typeName)
        {
            if (document == null || string.IsNullOrEmpty(familyName) || string.IsNullOrEmpty(typeName))
                return false;

            try
            {
                var family = GetFamily(document, familyName);
                var type = GetFamilyType(document, familyName, typeName);
                return family != null && type != null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating door family: {FamilyName}/{TypeName}", familyName, typeName);
                return false;
            }
        }

        /// <summary>
        /// Validate window family exists in document
        /// </summary>
        public bool ValidateWindowFamily(Document document, string familyName, string typeName)
        {
            if (document == null || string.IsNullOrEmpty(familyName) || string.IsNullOrEmpty(typeName))
                return false;

            try
            {
                var family = GetFamily(document, familyName);
                var type = GetFamilyType(document, familyName, typeName);
                return family != null && type != null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating window family: {FamilyName}/{TypeName}", familyName, typeName);
                return false;
            }
        }

        /// <summary>
        /// Get or create level by name
        /// </summary>
        public Level GetOrCreateLevel(Document document, string levelName, double elevation = 0.0)
        {
            if (document == null || string.IsNullOrEmpty(levelName))
                return null;

            try
            {
                // Try to find existing level
                var existingLevel = new FilteredElementCollector(document)
                    .OfClass(typeof(Level))
                    .Cast<Level>()
                    .FirstOrDefault(l => l.Name.Equals(levelName, StringComparison.OrdinalIgnoreCase));

                if (existingLevel != null)
                    return existingLevel;

                // Create new level
                var level = Level.Create(document, elevation);
                if (level != null)
                {
                    level.Name = levelName;
                    _logger.LogInformation("Created new level: {LevelName} at elevation {Elevation}", levelName, elevation);
                }

                return level;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting or creating level: {LevelName}", levelName);
                return null;
            }
        }

        #region Helper Methods

        private WallType GetWallType(Document document, string wallTypeName)
        {
            return new FilteredElementCollector(document)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault(wt => wt.Name.Equals(wallTypeName, StringComparison.OrdinalIgnoreCase));
        }

        private string GetDefaultWallType(Document document)
        {
            var defaultWallType = GetWallType(document, "Generic - 200mm");
            if (defaultWallType != null)
                return "Generic - 200mm";

            // Fallback to first available wall type
            var firstWallType = new FilteredElementCollector(document)
                .OfClass(typeof(WallType))
                .Cast<WallType>()
                .FirstOrDefault();

            return firstWallType?.Name ?? "Generic - 200mm";
        }

        private Family GetFamily(Document document, string familyName)
        {
            return new FilteredElementCollector(document)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.Name.Equals(familyName, StringComparison.OrdinalIgnoreCase));
        }

        private FamilySymbol GetFamilyType(Document document, string familyName, string typeName)
        {
            var family = GetFamily(document, familyName);
            if (family == null)
                return null;

            return family.GetFamilySymbolIds()
                .Select(id => document.GetElement(id) as FamilySymbol)
                .FirstOrDefault(ft => ft.Name.Equals(typeName, StringComparison.OrdinalIgnoreCase));
        }

        private (string familyName, string typeName) GetDefaultDoorFamily(Document document)
        {
            var doorFamily = new FilteredElementCollector(document)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.FamilyCategoryId.IntegerValue == (int)BuiltInCategory.OST_Doors);

            if (doorFamily != null)
            {
                var doorType = doorFamily.GetFamilySymbolIds()
                    .Select(id => document.GetElement(id) as FamilySymbol)
                    .FirstOrDefault();

                if (doorType != null)
                    return (doorFamily.Name, doorType.Name);
            }

            return ("Single-Flush", "0915 x 2134mm");
        }

        private (string familyName, string typeName) GetDefaultWindowFamily(Document document)
        {
            var windowFamily = new FilteredElementCollector(document)
                .OfClass(typeof(Family))
                .Cast<Family>()
                .FirstOrDefault(f => f.FamilyCategoryId.IntegerValue == (int)BuiltInCategory.OST_Windows);

            if (windowFamily != null)
            {
                var windowType = windowFamily.GetFamilySymbolIds()
                    .Select(id => document.GetElement(id) as FamilySymbol)
                    .FirstOrDefault();

                if (windowType != null)
                    return (windowFamily.Name, windowType.Name);
            }

            return ("Fixed", "1220 x 1830mm");
        }

        private T FindElementById<T>(Document document, string elementId) where T : Element
        {
            if (string.IsNullOrEmpty(elementId) || !int.TryParse(elementId, out int id))
                return null;

            try
            {
                var element = document.GetElement(new ElementId(id));
                return element as T;
            }
            catch
            {
                return null;
            }
        }

        private void SetElementParameters(Element element, Dictionary<string, object> parameters)
        {
            if (element == null || parameters == null || !parameters.Any())
                return;

            foreach (var param in parameters)
            {
                try
                {
                    var parameter = element.get_Parameter(param.Key);
                    if (parameter != null && !parameter.IsReadOnly)
                    {
                        if (param.Value is string stringValue)
                        {
                            parameter.Set(stringValue);
                        }
                        else if (param.Value is double doubleValue)
                        {
                            parameter.Set(doubleValue);
                        }
                        else if (param.Value is int intValue)
                        {
                            parameter.Set(intValue);
                        }
                        else if (param.Value is bool boolValue)
                        {
                            parameter.Set(boolValue ? 1 : 0);
                        }
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogWarning(ex, "Failed to set parameter {ParameterName} on element {ElementId}", 
                        param.Key, element.Id);
                }
            }
        }

        #endregion
    }
}
