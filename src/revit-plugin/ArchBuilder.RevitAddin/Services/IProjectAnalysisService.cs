using Autodesk.Revit.DB;
using System;
using System.Collections.Generic;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Interface for analyzing Revit projects and extracting metrics
    /// </summary>
    public interface IProjectAnalysisService
    {
        /// <summary>
        /// Analyze project and extract comprehensive metrics
        /// </summary>
        /// <param name="document">Revit document to analyze</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Project analysis result</returns>
        ProjectAnalysisResult AnalyzeProject(Document document, string correlationId);

        /// <summary>
        /// Extract element counts and basic metrics
        /// </summary>
        /// <param name="document">Revit document to analyze</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Element metrics</returns>
        ElementMetrics ExtractElementMetrics(Document document, string correlationId);

        /// <summary>
        /// Extract clash detection data
        /// </summary>
        /// <param name="document">Revit document to analyze</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Clash detection results</returns>
        ClashDetectionResult ExtractClashData(Document document, string correlationId);

        /// <summary>
        /// Extract performance metrics
        /// </summary>
        /// <param name="document">Revit document to analyze</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Performance metrics</returns>
        PerformanceMetrics ExtractPerformanceMetrics(Document document, string correlationId);

        /// <summary>
        /// Extract compliance issues
        /// </summary>
        /// <param name="document">Revit document to analyze</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Compliance issues</returns>
        ComplianceIssues ExtractComplianceIssues(Document document, string correlationId);
    }

    /// <summary>
    /// Comprehensive project analysis result
    /// </summary>
    public class ProjectAnalysisResult
    {
        public string ProjectName { get; set; }
        public string ProjectPath { get; set; }
        public DateTime AnalysisDate { get; set; }
        public ElementMetrics ElementMetrics { get; set; }
        public ClashDetectionResult ClashData { get; set; }
        public PerformanceMetrics PerformanceMetrics { get; set; }
        public ComplianceIssues ComplianceIssues { get; set; }
        public List<ImprovementRecommendation> Recommendations { get; set; } = new List<ImprovementRecommendation>();
        public string CorrelationId { get; set; }
    }

    /// <summary>
    /// Element metrics and counts
    /// </summary>
    public class ElementMetrics
    {
        public int TotalElements { get; set; }
        public int WallCount { get; set; }
        public int DoorCount { get; set; }
        public int WindowCount { get; set; }
        public int RoomCount { get; set; }
        public int FamilyCount { get; set; }
        public int LevelCount { get; set; }
        public int ViewCount { get; set; }
        public int SheetCount { get; set; }
        public Dictionary<string, int> WallTypes { get; set; } = new Dictionary<string, int>();
        public Dictionary<string, int> DoorTypes { get; set; } = new Dictionary<string, int>();
        public Dictionary<string, int> WindowTypes { get; set; } = new Dictionary<string, int>();
        public Dictionary<string, int> RoomTypes { get; set; } = new Dictionary<string, int>();
    }

    /// <summary>
    /// Clash detection results
    /// </summary>
    public class ClashDetectionResult
    {
        public int TotalClashes { get; set; }
        public int HardClashes { get; set; }
        public int SoftClashes { get; set; }
        public List<ClashDetail> Clashes { get; set; } = new List<ClashDetail>();
        public Dictionary<string, int> ClashCategories { get; set; } = new Dictionary<string, int>();
    }

    /// <summary>
    /// Performance metrics
    /// </summary>
    public class PerformanceMetrics
    {
        public double FileSizeMB { get; set; }
        public int ComplexFamilies { get; set; }
        public int UnusedElements { get; set; }
        public int LargeFamilies { get; set; }
        public int HeavyViews { get; set; }
        public double ModelComplexityScore { get; set; }
        public List<PerformanceIssue> Issues { get; set; } = new List<PerformanceIssue>();
    }

    /// <summary>
    /// Compliance issues
    /// </summary>
    public class ComplianceIssues
    {
        public int TotalIssues { get; set; }
        public int CriticalIssues { get; set; }
        public int WarningIssues { get; set; }
        public List<ComplianceIssue> Issues { get; set; } = new List<ComplianceIssue>();
        public Dictionary<string, int> IssueCategories { get; set; } = new Dictionary<string, int>();
    }

    /// <summary>
    /// Clash detail information
    /// </summary>
    public class ClashDetail
    {
        public string Id { get; set; }
        public string Element1Id { get; set; }
        public string Element2Id { get; set; }
        public string Element1Name { get; set; }
        public string Element2Name { get; set; }
        public string ClashType { get; set; }
        public string Severity { get; set; }
        public string Description { get; set; }
        public XYZ Location { get; set; }
    }

    /// <summary>
    /// Performance issue details
    /// </summary>
    public class PerformanceIssue
    {
        public string Type { get; set; }
        public string Description { get; set; }
        public string ElementId { get; set; }
        public string Severity { get; set; }
        public string Recommendation { get; set; }
    }

    /// <summary>
    /// Compliance issue details
    /// </summary>
    public class ComplianceIssue
    {
        public string Id { get; set; }
        public string Type { get; set; }
        public string Description { get; set; }
        public string ElementId { get; set; }
        public string Severity { get; set; }
        public string BuildingCode { get; set; }
        public string Recommendation { get; set; }
    }

    /// <summary>
    /// Improvement recommendation
    /// </summary>
    public class ImprovementRecommendation
    {
        public string Id { get; set; }
        public string Category { get; set; }
        public string Title { get; set; }
        public string Description { get; set; }
        public string Priority { get; set; }
        public string Impact { get; set; }
        public string Implementation { get; set; }
        public int EstimatedTimeHours { get; set; }
    }
}
