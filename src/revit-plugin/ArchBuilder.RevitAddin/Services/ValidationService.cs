using Autodesk.Revit.DB;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Service for validating Revit elements and operations
    /// </summary>
    public class ValidationService : IValidationService
    {
        private readonly ILogger<ValidationService> _logger;
        private readonly IConfigurationHelper _configHelper;

        // Validation constants
        private const double MIN_WALL_LENGTH_MM = 100;
        private const double MAX_WALL_LENGTH_MM = 50000;
        private const double MIN_WALL_HEIGHT_MM = 1000;
        private const double MAX_WALL_HEIGHT_MM = 5000;
        private const double MIN_DOOR_WIDTH_MM = 600;
        private const double MAX_DOOR_WIDTH_MM = 2000;
        private const double MIN_DOOR_HEIGHT_MM = 1800;
        private const double MAX_DOOR_HEIGHT_MM = 2500;
        private const double MIN_ROOM_AREA_M2 = 5.0;
        private const double MAX_ROOM_AREA_M2 = 1000.0;
        private const double MIN_CORRIDOR_WIDTH_MM = 1200;

        public ValidationService(ILogger<ValidationService> logger, IConfigurationHelper configHelper)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _configHelper = configHelper ?? throw new ArgumentNullException(nameof(configHelper));
        }

        /// <summary>
        /// Validate a single element
        /// </summary>
        public ElementValidationResult ValidateElement(Element element, string correlationId)
        {
            if (element == null)
                throw new ArgumentNullException(nameof(element));

            using var scope = _logger.BeginScope("ValidateElement {ElementId} {CorrelationId}", element.Id, correlationId);

            var result = new ElementValidationResult
            {
                ElementId = element.Id.ToString(),
                ElementType = element.GetType().Name
            };

            try
            {
                _logger.LogDebug("Validating element {ElementId} of type {ElementType}", element.Id, element.GetType().Name);

                // Basic element validation
                if (!element.IsValidObject)
                {
                    result.Errors.Add("Element is not valid");
                }

                // Element-specific validation
                switch (element)
                {
                    case Wall wall:
                        ValidateWall(wall, result);
                        break;
                    case FamilyInstance familyInstance:
                        ValidateFamilyInstance(familyInstance, result);
                        break;
                    case Room room:
                        ValidateRoom(room, result);
                        break;
                }

                result.IsValid = result.Errors.Count == 0;

                _logger.LogDebug("Element validation completed. Valid: {IsValid}, Errors: {ErrorCount}, Warnings: {WarningCount}",
                    result.IsValid, result.Errors.Count, result.Warnings.Count);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating element {ElementId}", element.Id);
                result.Errors.Add($"Validation error: {ex.Message}");
                result.IsValid = false;
                return result;
            }
        }

        /// <summary>
        /// Validate geometric constraints
        /// </summary>
        public GeometricValidationResult ValidateGeometry(IEnumerable<Wall> walls, string correlationId)
        {
            if (walls == null)
                throw new ArgumentNullException(nameof(walls));

            using var scope = _logger.BeginScope("ValidateGeometry {CorrelationId}", correlationId);

            var result = new GeometricValidationResult
            {
                WallCount = walls.Count()
            };

            try
            {
                _logger.LogInformation("Validating geometry for {WallCount} walls", result.WallCount);

                var wallList = walls.ToList();
                var totalLength = 0.0;

                foreach (var wall in wallList)
                {
                    try
                    {
                        // Validate wall length
                        var wallCurve = (wall.Location as LocationCurve)?.Curve;
                        if (wallCurve != null)
                        {
                            var length = wallCurve.Length;
                            totalLength += length;

                            if (length < MIN_WALL_LENGTH_MM / 1000.0) // Convert to meters
                            {
                                result.Issues.Add(new GeometricIssue
                                {
                                    Type = "WallTooShort",
                                    Description = $"Wall {wall.Id} is too short: {length:F2}m (minimum: {MIN_WALL_LENGTH_MM / 1000.0:F2}m)",
                                    ElementId = wall.Id.ToString(),
                                    Severity = "Error"
                                });
                                result.Errors.Add($"Wall {wall.Id} is too short");
                            }
                            else if (length > MAX_WALL_LENGTH_MM / 1000.0)
                            {
                                result.Issues.Add(new GeometricIssue
                                {
                                    Type = "WallTooLong",
                                    Description = $"Wall {wall.Id} is too long: {length:F2}m (maximum: {MAX_WALL_LENGTH_MM / 1000.0:F2}m)",
                                    ElementId = wall.Id.ToString(),
                                    Severity = "Warning"
                                });
                                result.Warnings.Add($"Wall {wall.Id} is very long");
                            }
                        }

                        // Validate wall height
                        var height = wall.get_Parameter(BuiltInParameter.WALL_USER_HEIGHT_PARAM)?.AsDouble();
                        if (height.HasValue)
                        {
                            if (height.Value < MIN_WALL_HEIGHT_MM / 1000.0)
                            {
                                result.Issues.Add(new GeometricIssue
                                {
                                    Type = "WallTooShort",
                                    Description = $"Wall {wall.Id} height is too low: {height.Value:F2}m (minimum: {MIN_WALL_HEIGHT_MM / 1000.0:F2}m)",
                                    ElementId = wall.Id.ToString(),
                                    Severity = "Error"
                                });
                                result.Errors.Add($"Wall {wall.Id} height is too low");
                            }
                            else if (height.Value > MAX_WALL_HEIGHT_MM / 1000.0)
                            {
                                result.Issues.Add(new GeometricIssue
                                {
                                    Type = "WallTooHigh",
                                    Description = $"Wall {wall.Id} height is too high: {height.Value:F2}m (maximum: {MAX_WALL_HEIGHT_MM / 1000.0:F2}m)",
                                    ElementId = wall.Id.ToString(),
                                    Severity = "Warning"
                                });
                                result.Warnings.Add($"Wall {wall.Id} height is very high");
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error validating wall {WallId}", wall.Id);
                        result.Errors.Add($"Error validating wall {wall.Id}: {ex.Message}");
                    }
                }

                // Check for overlapping walls
                CheckOverlappingWalls(wallList, result);

                result.TotalLength = totalLength;
                result.IsValid = result.Errors.Count == 0;

                _logger.LogInformation("Geometry validation completed. Valid: {IsValid}, Errors: {ErrorCount}, Warnings: {WarningCount}",
                    result.IsValid, result.Errors.Count, result.Warnings.Count);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during geometry validation");
                result.Errors.Add($"Geometry validation error: {ex.Message}");
                result.IsValid = false;
                return result;
            }
        }

        /// <summary>
        /// Validate building code compliance
        /// </summary>
        public BuildingCodeValidationResult ValidateBuildingCode(IEnumerable<Element> elements, string correlationId)
        {
            if (elements == null)
                throw new ArgumentNullException(nameof(elements));

            using var scope = _logger.BeginScope("ValidateBuildingCode {CorrelationId}", correlationId);

            var result = new BuildingCodeValidationResult
            {
                BuildingCode = "Turkish Building Code", // Default
                Region = "Turkey"
            };

            try
            {
                _logger.LogInformation("Validating building code compliance for {ElementCount} elements", elements.Count());

                var elementList = elements.ToList();

                // Check minimum room areas
                var rooms = elementList.OfType<Room>().ToList();
                foreach (var room in rooms)
                {
                    var area = room.get_Parameter(BuiltInParameter.ROOM_AREA)?.AsDouble();
                    if (area.HasValue && area.Value < MIN_ROOM_AREA_M2)
                    {
                        result.Violations.Add($"Room {room.Id} area {area.Value:F2}m² is below minimum {MIN_ROOM_AREA_M2}m²");
                    }
                }

                // Check door accessibility
                var doors = elementList.OfType<FamilyInstance>()
                    .Where(fi => fi.Category?.Id?.IntegerValue == (int)BuiltInCategory.OST_Doors)
                    .ToList();

                foreach (var door in doors)
                {
                    var width = door.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.AsDouble();
                    if (width.HasValue && width.Value < MIN_DOOR_WIDTH_MM / 1000.0)
                    {
                        result.Violations.Add($"Door {door.Id} width {width.Value * 1000:F0}mm is below minimum {MIN_DOOR_WIDTH_MM}mm");
                    }
                }

                // Check corridor widths (simplified)
                CheckCorridorWidths(rooms, result);

                result.IsCompliant = result.Violations.Count == 0;

                _logger.LogInformation("Building code validation completed. Compliant: {IsCompliant}, Violations: {ViolationCount}",
                    result.IsCompliant, result.Violations.Count);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during building code validation");
                result.Violations.Add($"Building code validation error: {ex.Message}");
                result.IsCompliant = false;
                return result;
            }
        }

        /// <summary>
        /// Validate accessibility requirements
        /// </summary>
        public AccessibilityValidationResult ValidateAccessibility(IEnumerable<FamilyInstance> doors, string correlationId)
        {
            if (doors == null)
                throw new ArgumentNullException(nameof(doors));

            using var scope = _logger.BeginScope("ValidateAccessibility {CorrelationId}", correlationId);

            var result = new AccessibilityValidationResult
            {
                Standard = "ADA Compliance"
            };

            try
            {
                _logger.LogInformation("Validating accessibility for {DoorCount} doors", doors.Count());

                var doorList = doors.ToList();
                var nonCompliantCount = 0;

                foreach (var door in doorList)
                {
                    try
                    {
                        var width = door.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.AsDouble();
                        var height = door.get_Parameter(BuiltInParameter.DOOR_HEIGHT)?.AsDouble();

                        if (width.HasValue && width.Value < 0.9) // 900mm minimum
                        {
                            result.Violations.Add($"Door {door.Id} width {width.Value * 1000:F0}mm is below accessibility minimum 900mm");
                            nonCompliantCount++;
                        }

                        if (height.HasValue && height.Value < 2.0) // 2000mm minimum
                        {
                            result.Violations.Add($"Door {door.Id} height {height.Value * 1000:F0}mm is below accessibility minimum 2000mm");
                            nonCompliantCount++;
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error validating door {DoorId} for accessibility", door.Id);
                        result.Violations.Add($"Error validating door {door.Id}: {ex.Message}");
                    }
                }

                result.NonCompliantDoors = nonCompliantCount;
                result.IsCompliant = result.Violations.Count == 0;

                _logger.LogInformation("Accessibility validation completed. Compliant: {IsCompliant}, Non-compliant doors: {NonCompliantCount}",
                    result.IsCompliant, result.NonCompliantDoors);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during accessibility validation");
                result.Violations.Add($"Accessibility validation error: {ex.Message}");
                result.IsCompliant = false;
                return result;
            }
        }

        /// <summary>
        /// Validate room areas
        /// </summary>
        public RoomAreaValidationResult ValidateRoomAreas(IEnumerable<Room> rooms, string correlationId)
        {
            if (rooms == null)
                throw new ArgumentNullException(nameof(rooms));

            using var scope = _logger.BeginScope("ValidateRoomAreas {CorrelationId}", correlationId);

            var result = new RoomAreaValidationResult
            {
                RoomCount = rooms.Count()
            };

            try
            {
                _logger.LogInformation("Validating room areas for {RoomCount} rooms", result.RoomCount);

                var roomList = rooms.ToList();
                var totalArea = 0.0;

                foreach (var room in roomList)
                {
                    try
                    {
                        var area = room.get_Parameter(BuiltInParameter.ROOM_AREA)?.AsDouble();
                        if (area.HasValue)
                        {
                            totalArea += area.Value;

                            if (area.Value < MIN_ROOM_AREA_M2)
                            {
                                result.Issues.Add(new RoomAreaIssue
                                {
                                    RoomId = room.Id.ToString(),
                                    RoomName = room.get_Parameter(BuiltInParameter.ROOM_NAME)?.AsString() ?? "Unknown",
                                    CurrentArea = area.Value,
                                    MinimumArea = MIN_ROOM_AREA_M2,
                                    IssueType = "BelowMinimum"
                                });
                                result.Errors.Add($"Room {room.Id} area {area.Value:F2}m² is below minimum {MIN_ROOM_AREA_M2}m²");
                            }
                            else if (area.Value > MAX_ROOM_AREA_M2)
                            {
                                result.Issues.Add(new RoomAreaIssue
                                {
                                    RoomId = room.Id.ToString(),
                                    RoomName = room.get_Parameter(BuiltInParameter.ROOM_NAME)?.AsString() ?? "Unknown",
                                    CurrentArea = area.Value,
                                    MinimumArea = MAX_ROOM_AREA_M2,
                                    IssueType = "AboveMaximum"
                                });
                                result.Warnings.Add($"Room {room.Id} area {area.Value:F2}m² is above maximum {MAX_ROOM_AREA_M2}m²");
                            }
                        }
                        else
                        {
                            result.Errors.Add($"Room {room.Id} has no area parameter");
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error validating room {RoomId} area", room.Id);
                        result.Errors.Add($"Error validating room {room.Id}: {ex.Message}");
                    }
                }

                result.TotalArea = totalArea;
                result.IsValid = result.Errors.Count == 0;

                _logger.LogInformation("Room area validation completed. Valid: {IsValid}, Total area: {TotalArea:F2}m², Issues: {IssueCount}",
                    result.IsValid, result.TotalArea, result.Issues.Count);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during room area validation");
                result.Errors.Add($"Room area validation error: {ex.Message}");
                result.IsValid = false;
                return result;
            }
        }

        #region Private Helper Methods

        private void ValidateWall(Wall wall, ElementValidationResult result)
        {
            try
            {
                var wallCurve = (wall.Location as LocationCurve)?.Curve;
                if (wallCurve == null)
                {
                    result.Errors.Add("Wall has no curve");
                    return;
                }

                var length = wallCurve.Length;
                if (length < MIN_WALL_LENGTH_MM / 1000.0)
                {
                    result.Errors.Add($"Wall length {length:F2}m is below minimum {MIN_WALL_LENGTH_MM / 1000.0:F2}m");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating wall {WallId}", wall.Id);
                result.Errors.Add($"Wall validation error: {ex.Message}");
            }
        }

        private void ValidateFamilyInstance(FamilyInstance familyInstance, ElementValidationResult result)
        {
            try
            {
                var category = familyInstance.Category;
                if (category == null)
                {
                    result.Warnings.Add("Family instance has no category");
                    return;
                }

                if (category.Id.IntegerValue == (int)BuiltInCategory.OST_Doors)
                {
                    var width = familyInstance.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.AsDouble();
                    if (width.HasValue && width.Value < MIN_DOOR_WIDTH_MM / 1000.0)
                    {
                        result.Errors.Add($"Door width {width.Value * 1000:F0}mm is below minimum {MIN_DOOR_WIDTH_MM}mm");
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating family instance {FamilyInstanceId}", familyInstance.Id);
                result.Errors.Add($"Family instance validation error: {ex.Message}");
            }
        }

        private void ValidateRoom(Room room, ElementValidationResult result)
        {
            try
            {
                var area = room.get_Parameter(BuiltInParameter.ROOM_AREA)?.AsDouble();
                if (area.HasValue && area.Value < MIN_ROOM_AREA_M2)
                {
                    result.Errors.Add($"Room area {area.Value:F2}m² is below minimum {MIN_ROOM_AREA_M2}m²");
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating room {RoomId}", room.Id);
                result.Errors.Add($"Room validation error: {ex.Message}");
            }
        }

        private void CheckOverlappingWalls(List<Wall> walls, GeometricValidationResult result)
        {
            // Simplified overlap check - in practice, this would be more sophisticated
            for (int i = 0; i < walls.Count; i++)
            {
                for (int j = i + 1; j < walls.Count; j++)
                {
                    try
                    {
                        var wall1Curve = (walls[i].Location as LocationCurve)?.Curve;
                        var wall2Curve = (walls[j].Location as LocationCurve)?.Curve;

                        if (wall1Curve != null && wall2Curve != null)
                        {
                            // Check if curves are too close (simplified check)
                            var distance = wall1Curve.Distance(wall2Curve);
                            if (distance < 0.1) // 100mm threshold
                            {
                                result.Issues.Add(new GeometricIssue
                                {
                                    Type = "OverlappingWalls",
                                    Description = $"Walls {walls[i].Id} and {walls[j].Id} are too close: {distance * 1000:F0}mm",
                                    ElementId = $"{walls[i].Id},{walls[j].Id}",
                                    Severity = "Warning"
                                });
                                result.Warnings.Add($"Walls {walls[i].Id} and {walls[j].Id} are very close");
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error checking overlap between walls {Wall1Id} and {Wall2Id}", walls[i].Id, walls[j].Id);
                    }
                }
            }
        }

        private void CheckCorridorWidths(List<Room> rooms, BuildingCodeValidationResult result)
        {
            // Simplified corridor width check
            // In practice, this would analyze circulation paths and check widths
            foreach (var room in rooms)
            {
                var area = room.get_Parameter(BuiltInParameter.ROOM_AREA)?.AsDouble();
                if (area.HasValue)
                {
                    // Simple heuristic: if room is very long and narrow, it might be a corridor
                    var roomName = room.get_Parameter(BuiltInParameter.ROOM_NAME)?.AsString()?.ToLower();
                    if (roomName != null && (roomName.Contains("corridor") || roomName.Contains("hallway")))
                    {
                        // This would need more sophisticated analysis in practice
                        result.Warnings.Add($"Corridor {room.Id} width should be verified (minimum {MIN_CORRIDOR_WIDTH_MM}mm)");
                    }
                }
            }
        }

        #endregion
    }
}
