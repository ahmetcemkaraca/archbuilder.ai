using Autodesk.Revit.DB;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Service for analyzing Revit projects and extracting comprehensive metrics
    /// </summary>
    public class ProjectAnalysisService : IProjectAnalysisService
    {
        private readonly ILogger<ProjectAnalysisService> _logger;
        private readonly IValidationService _validationService;

        public ProjectAnalysisService(ILogger<ProjectAnalysisService> logger, IValidationService validationService)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _validationService = validationService ?? throw new ArgumentNullException(nameof(validationService));
        }

        /// <summary>
        /// Analyze project and extract comprehensive metrics
        /// </summary>
        public ProjectAnalysisResult AnalyzeProject(Document document, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));

            using var scope = _logger.BeginScope("AnalyzeProject {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Starting comprehensive project analysis");

                var result = new ProjectAnalysisResult
                {
                    ProjectName = document.Title,
                    ProjectPath = document.PathName,
                    AnalysisDate = DateTime.UtcNow,
                    CorrelationId = correlationId
                };

                // Extract element metrics
                result.ElementMetrics = ExtractElementMetrics(document, correlationId);

                // Extract clash data
                result.ClashData = ExtractClashData(document, correlationId);

                // Extract performance metrics
                result.PerformanceMetrics = ExtractPerformanceMetrics(document, correlationId);

                // Extract compliance issues
                result.ComplianceIssues = ExtractComplianceIssues(document, correlationId);

                // Generate improvement recommendations
                result.Recommendations = GenerateRecommendations(result);

                _logger.LogInformation("Project analysis completed successfully. Elements: {ElementCount}, Clashes: {ClashCount}, Issues: {IssueCount}",
                    result.ElementMetrics.TotalElements, result.ClashData.TotalClashes, result.ComplianceIssues.TotalIssues);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during project analysis");
                throw;
            }
        }

        /// <summary>
        /// Extract element counts and basic metrics
        /// </summary>
        public ElementMetrics ExtractElementMetrics(Document document, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));

            using var scope = _logger.BeginScope("ExtractElementMetrics {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Extracting element metrics");

                var metrics = new ElementMetrics();

                // Get all elements
                var allElements = new FilteredElementCollector(document).ToElements();
                metrics.TotalElements = allElements.Count;

                // Count specific element types
                metrics.WallCount = new FilteredElementCollector(document).OfClass(typeof(Wall)).GetElementCount();
                metrics.DoorCount = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_Doors).GetElementCount();
                metrics.WindowCount = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_Windows).GetElementCount();
                metrics.RoomCount = new FilteredElementCollector(document).OfClass(typeof(Room)).GetElementCount();
                metrics.FamilyCount = new FilteredElementCollector(document).OfClass(typeof(Family)).GetElementCount();
                metrics.LevelCount = new FilteredElementCollector(document).OfClass(typeof(Level)).GetElementCount();
                metrics.ViewCount = new FilteredElementCollector(document).OfClass(typeof(View)).GetElementCount();
                metrics.SheetCount = new FilteredElementCollector(document).OfClass(typeof(ViewSheet)).GetElementCount();

                // Analyze wall types
                var walls = new FilteredElementCollector(document).OfClass(typeof(Wall)).Cast<Wall>();
                foreach (var wall in walls)
                {
                    var wallType = wall.WallType;
                    if (wallType != null)
                    {
                        var typeName = wallType.Name;
                        metrics.WallTypes[typeName] = metrics.WallTypes.GetValueOrDefault(typeName, 0) + 1;
                    }
                }

                // Analyze door types
                var doors = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilyInstance>();
                foreach (var door in doors)
                {
                    var symbol = door.Symbol;
                    if (symbol != null)
                    {
                        var typeName = symbol.Name;
                        metrics.DoorTypes[typeName] = metrics.DoorTypes.GetValueOrDefault(typeName, 0) + 1;
                    }
                }

                // Analyze window types
                var windows = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_Windows).Cast<FamilyInstance>();
                foreach (var window in windows)
                {
                    var symbol = window.Symbol;
                    if (symbol != null)
                    {
                        var typeName = symbol.Name;
                        metrics.WindowTypes[typeName] = metrics.WindowTypes.GetValueOrDefault(typeName, 0) + 1;
                    }
                }

                // Analyze room types
                var rooms = new FilteredElementCollector(document).OfClass(typeof(Room)).Cast<Room>();
                foreach (var room in rooms)
                {
                    var roomType = room.get_Parameter(BuiltInParameter.ROOM_TYPE)?.AsString() ?? "Unknown";
                    metrics.RoomTypes[roomType] = metrics.RoomTypes.GetValueOrDefault(roomType, 0) + 1;
                }

                _logger.LogInformation("Element metrics extracted. Total: {TotalElements}, Walls: {WallCount}, Doors: {DoorCount}, Windows: {WindowCount}, Rooms: {RoomCount}",
                    metrics.TotalElements, metrics.WallCount, metrics.DoorCount, metrics.WindowCount, metrics.RoomCount);

                return metrics;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error extracting element metrics");
                throw;
            }
        }

        /// <summary>
        /// Extract clash detection data
        /// </summary>
        public ClashDetectionResult ExtractClashData(Document document, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));

            using var scope = _logger.BeginScope("ExtractClashData {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Extracting clash detection data");

                var result = new ClashDetectionResult();

                // This is a simplified clash detection implementation
                // In practice, you would use Navisworks API or similar tools
                var clashes = DetectClashes(document);
                result.Clashes = clashes;
                result.TotalClashes = clashes.Count;
                result.HardClashes = clashes.Count(c => c.Severity == "Critical");
                result.SoftClashes = clashes.Count(c => c.Severity == "Warning");

                // Categorize clashes
                foreach (var clash in clashes)
                {
                    var category = clash.ClashType;
                    result.ClashCategories[category] = result.ClashCategories.GetValueOrDefault(category, 0) + 1;
                }

                _logger.LogInformation("Clash data extracted. Total clashes: {TotalClashes}, Hard: {HardClashes}, Soft: {SoftClashes}",
                    result.TotalClashes, result.HardClashes, result.SoftClashes);

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error extracting clash data");
                throw;
            }
        }

        /// <summary>
        /// Extract performance metrics
        /// </summary>
        public PerformanceMetrics ExtractPerformanceMetrics(Document document, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));

            using var scope = _logger.BeginScope("ExtractPerformanceMetrics {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Extracting performance metrics");

                var metrics = new PerformanceMetrics();

                // Get file size
                if (!string.IsNullOrEmpty(document.PathName) && File.Exists(document.PathName))
                {
                    var fileInfo = new FileInfo(document.PathName);
                    metrics.FileSizeMB = fileInfo.Length / (1024.0 * 1024.0);
                }

                // Count complex families (families with many parameters)
                var families = new FilteredElementCollector(document).OfClass(typeof(Family)).Cast<Family>();
                foreach (var family in families)
                {
                    var parameterCount = family.GetParameters().Count();
                    if (parameterCount > 50) // Threshold for complex families
                    {
                        metrics.ComplexFamilies++;
                    }
                }

                // Count unused elements (simplified)
                var allElements = new FilteredElementCollector(document).ToElements();
                var unusedCount = 0;
                foreach (var element in allElements)
                {
                    // Simplified check - in practice, this would be more sophisticated
                    if (!element.IsValidObject)
                    {
                        unusedCount++;
                    }
                }
                metrics.UnusedElements = unusedCount;

                // Count large families (families with many instances)
                var familyInstances = new FilteredElementCollector(document).OfClass(typeof(FamilyInstance)).Cast<FamilyInstance>();
                var familyGroups = familyInstances.GroupBy(fi => fi.Symbol?.Family?.Name).Where(g => g.Count() > 100);
                metrics.LargeFamilies = familyGroups.Count();

                // Count heavy views (views with many elements)
                var views = new FilteredElementCollector(document).OfClass(typeof(View)).Cast<View>();
                foreach (var view in views)
                {
                    var elementCount = new FilteredElementCollector(document, view.Id).GetElementCount();
                    if (elementCount > 1000) // Threshold for heavy views
                    {
                        metrics.HeavyViews++;
                    }
                }

                // Calculate model complexity score
                metrics.ModelComplexityScore = CalculateComplexityScore(metrics);

                // Identify performance issues
                metrics.Issues = IdentifyPerformanceIssues(metrics);

                _logger.LogInformation("Performance metrics extracted. File size: {FileSizeMB:F2}MB, Complex families: {ComplexFamilies}, Unused elements: {UnusedElements}",
                    metrics.FileSizeMB, metrics.ComplexFamilies, metrics.UnusedElements);

                return metrics;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error extracting performance metrics");
                throw;
            }
        }

        /// <summary>
        /// Extract compliance issues
        /// </summary>
        public ComplianceIssues ExtractComplianceIssues(Document document, string correlationId)
        {
            if (document == null)
                throw new ArgumentNullException(nameof(document));

            using var scope = _logger.BeginScope("ExtractComplianceIssues {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Extracting compliance issues");

                var issues = new ComplianceIssues();

                // Check room areas
                var rooms = new FilteredElementCollector(document).OfClass(typeof(Room)).Cast<Room>();
                foreach (var room in rooms)
                {
                    var area = room.get_Parameter(BuiltInParameter.ROOM_AREA)?.AsDouble();
                    if (area.HasValue && area.Value < 5.0) // Minimum room area
                    {
                        issues.Issues.Add(new ComplianceIssue
                        {
                            Id = Guid.NewGuid().ToString(),
                            Type = "RoomArea",
                            Description = $"Room {room.Id} area {area.Value:F2}m² is below minimum 5.0m²",
                            ElementId = room.Id.ToString(),
                            Severity = "Critical",
                            BuildingCode = "Turkish Building Code",
                            Recommendation = "Increase room area or combine with adjacent room"
                        });
                    }
                }

                // Check door accessibility
                var doors = new FilteredElementCollector(document).OfCategory(BuiltInCategory.OST_Doors).Cast<FamilyInstance>();
                foreach (var door in doors)
                {
                    var width = door.get_Parameter(BuiltInParameter.DOOR_WIDTH)?.AsDouble();
                    if (width.HasValue && width.Value < 0.9) // 900mm minimum
                    {
                        issues.Issues.Add(new ComplianceIssue
                        {
                            Id = Guid.NewGuid().ToString(),
                            Type = "DoorWidth",
                            Description = $"Door {door.Id} width {width.Value * 1000:F0}mm is below accessibility minimum 900mm",
                            ElementId = door.Id.ToString(),
                            Severity = "Critical",
                            BuildingCode = "Accessibility Standards",
                            Recommendation = "Increase door width to minimum 900mm"
                        });
                    }
                }

                // Categorize issues
                issues.TotalIssues = issues.Issues.Count;
                issues.CriticalIssues = issues.Issues.Count(i => i.Severity == "Critical");
                issues.WarningIssues = issues.Issues.Count(i => i.Severity == "Warning");

                foreach (var issue in issues.Issues)
                {
                    issues.IssueCategories[issue.Type] = issues.IssueCategories.GetValueOrDefault(issue.Type, 0) + 1;
                }

                _logger.LogInformation("Compliance issues extracted. Total: {TotalIssues}, Critical: {CriticalIssues}, Warnings: {WarningIssues}",
                    issues.TotalIssues, issues.CriticalIssues, issues.WarningIssues);

                return issues;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error extracting compliance issues");
                throw;
            }
        }

        #region Private Helper Methods

        private List<ClashDetail> DetectClashes(Document document)
        {
            var clashes = new List<ClashDetail>();

            // Simplified clash detection - in practice, this would use Navisworks API
            // or other clash detection tools
            var walls = new FilteredElementCollector(document).OfClass(typeof(Wall)).Cast<Wall>().ToList();
            
            for (int i = 0; i < walls.Count; i++)
            {
                for (int j = i + 1; j < walls.Count; j++)
                {
                    try
                    {
                        var wall1 = walls[i];
                        var wall2 = walls[j];
                        
                        var curve1 = (wall1.Location as LocationCurve)?.Curve;
                        var curve2 = (wall2.Location as LocationCurve)?.Curve;
                        
                        if (curve1 != null && curve2 != null)
                        {
                            var distance = curve1.Distance(curve2);
                            if (distance < 0.05) // 50mm threshold
                            {
                                clashes.Add(new ClashDetail
                                {
                                    Id = Guid.NewGuid().ToString(),
                                    Element1Id = wall1.Id.ToString(),
                                    Element2Id = wall2.Id.ToString(),
                                    Element1Name = $"Wall {wall1.Id}",
                                    Element2Name = $"Wall {wall2.Id}",
                                    ClashType = "Wall Intersection",
                                    Severity = distance < 0.01 ? "Critical" : "Warning",
                                    Description = $"Walls are too close: {distance * 1000:F0}mm",
                                    Location = curve1.Evaluate(0.5) // Midpoint of first curve
                                });
                            }
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Error detecting clash between walls {Wall1Id} and {Wall2Id}", walls[i].Id, walls[j].Id);
                    }
                }
            }

            return clashes;
        }

        private double CalculateComplexityScore(PerformanceMetrics metrics)
        {
            // Simplified complexity calculation
            var score = 0.0;
            
            // File size factor
            score += Math.Min(metrics.FileSizeMB / 100.0, 5.0);
            
            // Complex families factor
            score += Math.Min(metrics.ComplexFamilies / 10.0, 3.0);
            
            // Unused elements factor
            score += Math.Min(metrics.UnusedElements / 100.0, 2.0);
            
            // Large families factor
            score += Math.Min(metrics.LargeFamilies / 5.0, 2.0);
            
            // Heavy views factor
            score += Math.Min(metrics.HeavyViews / 5.0, 2.0);
            
            return Math.Min(score, 10.0); // Cap at 10
        }

        private List<PerformanceIssue> IdentifyPerformanceIssues(PerformanceMetrics metrics)
        {
            var issues = new List<PerformanceIssue>();

            if (metrics.FileSizeMB > 200)
            {
                issues.Add(new PerformanceIssue
                {
                    Type = "LargeFileSize",
                    Description = $"File size {metrics.FileSizeMB:F2}MB is very large",
                    Severity = "Warning",
                    Recommendation = "Consider purging unused elements and optimizing families"
                });
            }

            if (metrics.ComplexFamilies > 20)
            {
                issues.Add(new PerformanceIssue
                {
                    Type = "TooManyComplexFamilies",
                    Description = $"{metrics.ComplexFamilies} families are overly complex",
                    Severity = "Warning",
                    Recommendation = "Simplify family parameters and remove unused parameters"
                });
            }

            if (metrics.UnusedElements > 50)
            {
                issues.Add(new PerformanceIssue
                {
                    Type = "TooManyUnusedElements",
                    Description = $"{metrics.UnusedElements} unused elements found",
                    Severity = "Warning",
                    Recommendation = "Purge unused elements to improve performance"
                });
            }

            if (metrics.HeavyViews > 5)
            {
                issues.Add(new PerformanceIssue
                {
                    Type = "TooManyHeavyViews",
                    Description = $"{metrics.HeavyViews} views are performance-heavy",
                    Severity = "Warning",
                    Recommendation = "Optimize view settings and hide unnecessary elements"
                });
            }

            return issues;
        }

        private List<ImprovementRecommendation> GenerateRecommendations(ProjectAnalysisResult analysis)
        {
            var recommendations = new List<ImprovementRecommendation>();

            // Performance recommendations
            if (analysis.PerformanceMetrics.FileSizeMB > 100)
            {
                recommendations.Add(new ImprovementRecommendation
                {
                    Id = Guid.NewGuid().ToString(),
                    Category = "Performance",
                    Title = "Optimize File Size",
                    Description = "File size is large and may impact performance",
                    Priority = "High",
                    Impact = "Significant performance improvement",
                    Implementation = "Purge unused elements, optimize families, compress images",
                    EstimatedTimeHours = 4
                });
            }

            // Compliance recommendations
            if (analysis.ComplianceIssues.CriticalIssues > 0)
            {
                recommendations.Add(new ImprovementRecommendation
                {
                    Id = Guid.NewGuid().ToString(),
                    Category = "Compliance",
                    Title = "Fix Critical Compliance Issues",
                    Description = $"{analysis.ComplianceIssues.CriticalIssues} critical compliance issues found",
                    Priority = "Critical",
                    Impact = "Ensure building code compliance",
                    Implementation = "Review and fix all critical compliance issues",
                    EstimatedTimeHours = 8
                });
            }

            // Clash recommendations
            if (analysis.ClashData.TotalClashes > 0)
            {
                recommendations.Add(new ImprovementRecommendation
                {
                    Id = Guid.NewGuid().ToString(),
                    Category = "Coordination",
                    Title = "Resolve Clashes",
                    Description = $"{analysis.ClashData.TotalClashes} clashes detected",
                    Priority = "High",
                    Impact = "Improve coordination and reduce construction issues",
                    Implementation = "Review and resolve all clashes using Navisworks or similar tools",
                    EstimatedTimeHours = 6
                });
            }

            return recommendations;
        }

        #endregion
    }
}
