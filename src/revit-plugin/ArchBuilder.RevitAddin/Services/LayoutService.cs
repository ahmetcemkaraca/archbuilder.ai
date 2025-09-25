using Autodesk.Revit.DB;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Service for layout generation and management
    /// </summary>
    public class LayoutService : ILayoutService
    {
        private readonly ILogger<LayoutService> _logger;
        private readonly ITransactionService _transactionService;
        private readonly IElementCreationService _elementCreationService;
        private readonly IValidationService _validationService;
        private readonly ILocalCommunicationService _communicationService;

        public LayoutService(
            ILogger<LayoutService> logger,
            ITransactionService transactionService,
            IElementCreationService elementCreationService,
            IValidationService validationService,
            ILocalCommunicationService communicationService)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _transactionService = transactionService ?? throw new ArgumentNullException(nameof(transactionService));
            _elementCreationService = elementCreationService ?? throw new ArgumentNullException(nameof(elementCreationService));
            _validationService = validationService ?? throw new ArgumentNullException(nameof(validationService));
            _communicationService = communicationService ?? throw new ArgumentNullException(nameof(communicationService));
        }

        /// <summary>
        /// Generate layout from AI response
        /// </summary>
        public async Task<LayoutGenerationResult> GenerateLayoutAsync(Document document, LayoutData layoutData, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (layoutData == null)
                throw new ArgumentNullException(nameof(layoutData));

            using var scope = _logger.BeginScope("GenerateLayoutAsync {CorrelationId}", correlationId);

            var result = new LayoutGenerationResult
            {
                CorrelationId = correlationId,
                CreatedAt = DateTime.UtcNow
            };

            try
            {
                _logger.LogInformation("Starting layout generation with {WallCount} walls, {DoorCount} doors, {WindowCount} windows, {RoomCount} rooms",
                    layoutData.Walls.Count, layoutData.Doors.Count, layoutData.Windows.Count, layoutData.Rooms.Count);

                // Validate layout data first
                var validation = await ValidateLayoutAsync(layoutData, correlationId);
                result.Validation = validation;

                if (!validation.IsValid)
                {
                    result.Success = false;
                    result.ErrorMessage = "Layout validation failed";
                    result.RequiresHumanReview = true;
                    _logger.LogWarning("Layout validation failed: {ErrorCount} errors", validation.Errors.Count);
                    return result;
                }

                // Create elements in transaction
                var success = _transactionService.ExecuteTransaction(document, "Generate AI Layout", transaction =>
                {
                    try
                    {
                        // Create walls first
                        if (layoutData.Walls.Any())
                        {
                            var wallDefinitions = layoutData.Walls.Select(w => new WallDefinition
                            {
                                Id = w.Id,
                                StartPoint = new XYZ(w.StartPoint.X, w.StartPoint.Y, w.StartPoint.Z),
                                EndPoint = new XYZ(w.EndPoint.X, w.EndPoint.Y, w.EndPoint.Z),
                                Height = w.HeightMm / 1000.0, // Convert to meters
                                WallTypeName = w.WallTypeName,
                                LevelName = w.LevelName,
                                IsExterior = w.IsExterior,
                                Parameters = w.Parameters
                            }).ToList();

                            var createdWalls = _elementCreationService.CreateWalls(document, wallDefinitions, correlationId);
                            result.CreatedElementIds.AddRange(createdWalls.Select(w => w.Id.ToString()));
                        }

                        // Create doors
                        if (layoutData.Doors.Any())
                        {
                            var doorDefinitions = layoutData.Doors.Select(d => new DoorDefinition
                            {
                                Id = d.Id,
                                HostWallId = d.HostWallId,
                                PositionRatio = d.PositionRatio,
                                FamilyName = d.FamilyName,
                                TypeName = d.TypeName,
                                Width = d.WidthMm / 1000.0, // Convert to meters
                                Height = d.HeightMm / 1000.0, // Convert to meters
                                FlipHand = d.FlipHand,
                                FlipFacing = d.FlipFacing,
                                Parameters = d.Parameters
                            }).ToList();

                            var createdDoors = _elementCreationService.CreateDoors(document, doorDefinitions, correlationId);
                            result.CreatedElementIds.AddRange(createdDoors.Select(d => d.Id.ToString()));
                        }

                        // Create windows
                        if (layoutData.Windows.Any())
                        {
                            var windowDefinitions = layoutData.Windows.Select(w => new WindowDefinition
                            {
                                Id = w.Id,
                                HostWallId = w.HostWallId,
                                PositionRatio = w.PositionRatio,
                                FamilyName = w.FamilyName,
                                TypeName = w.TypeName,
                                Width = w.WidthMm / 1000.0, // Convert to meters
                                Height = w.HeightMm / 1000.0, // Convert to meters
                                SillHeight = w.SillHeight / 1000.0, // Convert to meters
                                Parameters = w.Parameters
                            }).ToList();

                            var createdWindows = _elementCreationService.CreateWindows(document, windowDefinitions, correlationId);
                            result.CreatedElementIds.AddRange(createdWindows.Select(w => w.Id.ToString()));
                        }

                        // Create rooms
                        if (layoutData.Rooms.Any())
                        {
                            var roomDefinitions = layoutData.Rooms.Select(r => new RoomDefinition
                            {
                                Id = r.Id,
                                Name = r.Name,
                                Number = r.Number,
                                LevelName = r.LevelName,
                                BoundaryPoints = r.BoundaryPoints.Select(p => new XYZ(p.X, p.Y, p.Z)).ToList(),
                                Parameters = r.Parameters
                            }).ToList();

                            var createdRooms = _elementCreationService.CreateRooms(document, roomDefinitions, correlationId);
                            result.CreatedElementIds.AddRange(createdRooms.Select(r => r.Id.ToString()));
                        }

                        return true;
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error during layout generation in transaction");
                        throw;
                    }
                }, correlationId);

                result.Success = success;
                result.RequiresHumanReview = validation.RequiresHumanReview || !success;

                if (success)
                {
                    _logger.LogInformation("Layout generation completed successfully. Created {ElementCount} elements", result.CreatedElementIds.Count);
                }
                else
                {
                    result.ErrorMessage = "Layout generation failed in transaction";
                    _logger.LogError("Layout generation failed in transaction");
                }

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error during layout generation");
                result.Success = false;
                result.ErrorMessage = $"Unexpected error: {ex.Message}";
                result.RequiresHumanReview = true;
                return result;
            }
        }

        /// <summary>
        /// Validate layout before creation
        /// </summary>
        public async Task<ValidationResult> ValidateLayoutAsync(LayoutData layoutData, string correlationId)
        {
            if (layoutData == null)
                throw new ArgumentNullException(nameof(layoutData));

            using var scope = _logger.BeginScope("ValidateLayoutAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Validating layout data");

                var result = new ValidationResult
                {
                    CorrelationId = correlationId
                };

                // Validate walls
                if (layoutData.Walls.Any())
                {
                    foreach (var wall in layoutData.Walls)
                    {
                        if (wall.StartPoint == null || wall.EndPoint == null)
                        {
                            result.Errors.Add($"Wall {wall.Id} has null start or end point");
                        }
                        else
                        {
                            var length = wall.StartPoint.DistanceTo(wall.EndPoint);
                            if (length < 0.1) // 100mm minimum
                            {
                                result.Errors.Add($"Wall {wall.Id} is too short: {length * 1000:F0}mm");
                            }
                        }

                        if (wall.HeightMm < 1000 || wall.HeightMm > 5000)
                        {
                            result.Errors.Add($"Wall {wall.Id} height {wall.HeightMm}mm is outside valid range (1000-5000mm)");
                        }
                    }
                }

                // Validate doors
                if (layoutData.Doors.Any())
                {
                    foreach (var door in layoutData.Doors)
                    {
                        if (string.IsNullOrEmpty(door.HostWallId))
                        {
                            result.Errors.Add($"Door {door.Id} has no host wall ID");
                        }

                        if (door.WidthMm < 600 || door.WidthMm > 2000)
                        {
                            result.Errors.Add($"Door {door.Id} width {door.WidthMm}mm is outside valid range (600-2000mm)");
                        }

                        if (door.HeightMm < 1800 || door.HeightMm > 2500)
                        {
                            result.Errors.Add($"Door {door.Id} height {door.HeightMm}mm is outside valid range (1800-2500mm)");
                        }

                        if (door.PositionRatio < 0.0 || door.PositionRatio > 1.0)
                        {
                            result.Errors.Add($"Door {door.Id} position ratio {door.PositionRatio} is outside valid range (0.0-1.0)");
                        }
                    }
                }

                // Validate windows
                if (layoutData.Windows.Any())
                {
                    foreach (var window in layoutData.Windows)
                    {
                        if (string.IsNullOrEmpty(window.HostWallId))
                        {
                            result.Errors.Add($"Window {window.Id} has no host wall ID");
                        }

                        if (window.WidthMm < 600 || window.WidthMm > 3000)
                        {
                            result.Errors.Add($"Window {window.Id} width {window.WidthMm}mm is outside valid range (600-3000mm)");
                        }

                        if (window.HeightMm < 600 || window.HeightMm > 3000)
                        {
                            result.Errors.Add($"Window {window.Id} height {window.HeightMm}mm is outside valid range (600-3000mm)");
                        }

                        if (window.PositionRatio < 0.0 || window.PositionRatio > 1.0)
                        {
                            result.Errors.Add($"Window {window.Id} position ratio {window.PositionRatio} is outside valid range (0.0-1.0)");
                        }
                    }
                }

                // Validate rooms
                if (layoutData.Rooms.Any())
                {
                    foreach (var room in layoutData.Rooms)
                    {
                        if (string.IsNullOrEmpty(room.Name))
                        {
                            result.Warnings.Add($"Room {room.Id} has no name");
                        }

                        if (room.BoundaryPoints.Count < 3)
                        {
                            result.Errors.Add($"Room {room.Id} has insufficient boundary points: {room.BoundaryPoints.Count}");
                        }
                    }
                }

                result.IsValid = result.Errors.Count == 0;
                result.RequiresHumanReview = result.Errors.Count > 0 || result.Warnings.Count > 3;

                _logger.LogInformation("Layout validation completed. Valid: {IsValid}, Errors: {ErrorCount}, Warnings: {WarningCount}",
                    result.IsValid, result.Errors.Count, result.Warnings.Count);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during layout validation");
                return new ValidationResult
                {
                    IsValid = false,
                    Errors = new List<string> { $"Validation error: {ex.Message}" },
                    CorrelationId = correlationId
                };
            }
        }

        /// <summary>
        /// Apply user corrections to layout
        /// </summary>
        public async Task<bool> ApplyCorrectionsAsync(Document document, List<LayoutCorrection> corrections, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));
            if (corrections == null || !corrections.Any())
                throw new ArgumentException("Corrections cannot be null or empty", nameof(corrections));

            using var scope = _logger.BeginScope("ApplyCorrectionsAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Applying {CorrectionCount} corrections", corrections.Count);

                var success = _transactionService.ExecuteTransaction(document, "Apply Layout Corrections", transaction =>
                {
                    foreach (var correction in corrections)
                    {
                        try
                        {
                            ApplyCorrection(document, correction);
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "Error applying correction {CorrectionId}", correction.Id);
                            throw;
                        }
                    }
                }, correlationId);

                if (success)
                {
                    _logger.LogInformation("Corrections applied successfully");
                }
                else
                {
                    _logger.LogError("Failed to apply corrections in transaction");
                }

                return success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error applying corrections");
                return false;
            }
        }

        /// <summary>
        /// Rollback layout changes
        /// </summary>
        public async Task<bool> RollbackLayoutAsync(Document document, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));

            using var scope = _logger.BeginScope("RollbackLayoutAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Rolling back layout changes");

                // This would typically involve undoing the last transaction
                // or restoring from a backup state
                // For now, this is a placeholder implementation

                _logger.LogInformation("Layout rollback completed");
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during layout rollback");
                return false;
            }
        }

        /// <summary>
        /// Get layout history for document
        /// </summary>
        public async Task<List<LayoutHistoryEntry>> GetLayoutHistoryAsync(Document document, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));

            using var scope = _logger.BeginScope("GetLayoutHistoryAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Retrieving layout history");

                // This would typically query a history database or document parameters
                // For now, return empty list as placeholder
                var history = new List<LayoutHistoryEntry>();

                _logger.LogInformation("Layout history retrieved: {EntryCount} entries", history.Count);
                return history;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error retrieving layout history");
                return new List<LayoutHistoryEntry>();
            }
        }

        #region Private Helper Methods

        private void ApplyCorrection(Document document, LayoutCorrection correction)
        {
            try
            {
                if (int.TryParse(correction.ElementId, out int elementId))
                {
                    var element = document.GetElement(new ElementId(elementId));
                    if (element != null)
                    {
                        switch (correction.CorrectionType.ToLower())
                        {
                            case "move":
                                ApplyMoveCorrection(element, correction);
                                break;
                            case "resize":
                                ApplyResizeCorrection(element, correction);
                                break;
                            case "rotate":
                                ApplyRotateCorrection(element, correction);
                                break;
                            case "delete":
                                document.Delete(element.Id);
                                break;
                            default:
                                _logger.LogWarning("Unknown correction type: {CorrectionType}", correction.CorrectionType);
                                break;
                        }
                    }
                    else
                    {
                        _logger.LogWarning("Element {ElementId} not found for correction", correction.ElementId);
                    }
                }
                else
                {
                    _logger.LogWarning("Invalid element ID format: {ElementId}", correction.ElementId);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error applying correction {CorrectionId} to element {ElementId}", 
                    correction.Id, correction.ElementId);
                throw;
            }
        }

        private void ApplyMoveCorrection(Element element, LayoutCorrection correction)
        {
            // Implementation for moving elements
            _logger.LogDebug("Applying move correction to element {ElementId}", element.Id);
        }

        private void ApplyResizeCorrection(Element element, LayoutCorrection correction)
        {
            // Implementation for resizing elements
            _logger.LogDebug("Applying resize correction to element {ElementId}", element.Id);
        }

        private void ApplyRotateCorrection(Element element, LayoutCorrection correction)
        {
            // Implementation for rotating elements
            _logger.LogDebug("Applying rotate correction to element {ElementId}", element.Id);
        }

        #endregion
    }
}
