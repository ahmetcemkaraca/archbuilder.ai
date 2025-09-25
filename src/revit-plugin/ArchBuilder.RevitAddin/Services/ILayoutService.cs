using Autodesk.Revit.DB;
using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Interface for layout generation and management
    /// </summary>
    public interface ILayoutService
    {
        /// <summary>
        /// Generate layout from AI response
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="layoutData">Layout data from AI</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Layout generation result</returns>
        Task<LayoutGenerationResult> GenerateLayoutAsync(Document document, LayoutData layoutData, string correlationId);

        /// <summary>
        /// Validate layout before creation
        /// </summary>
        /// <param name="layoutData">Layout data to validate</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Validation result</returns>
        Task<ValidationResult> ValidateLayoutAsync(LayoutData layoutData, string correlationId);

        /// <summary>
        /// Apply user corrections to layout
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="corrections">User corrections</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>True if corrections applied successfully</returns>
        Task<bool> ApplyCorrectionsAsync(Document document, List<LayoutCorrection> corrections, string correlationId);

        /// <summary>
        /// Rollback layout changes
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>True if rollback successful</returns>
        Task<bool> RollbackLayoutAsync(Document document, string correlationId);

        /// <summary>
        /// Get layout history for document
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Layout history</returns>
        Task<List<LayoutHistoryEntry>> GetLayoutHistoryAsync(Document document, string correlationId);
    }

    /// <summary>
    /// Layout generation result
    /// </summary>
    public class LayoutGenerationResult
    {
        public bool Success { get; set; }
        public string ErrorMessage { get; set; }
        public List<string> CreatedElementIds { get; set; } = new List<string>();
        public ValidationResult Validation { get; set; }
        public bool RequiresHumanReview { get; set; }
        public DateTime CreatedAt { get; set; }
        public string CorrelationId { get; set; }
    }

    /// <summary>
    /// Layout correction
    /// </summary>
    public class LayoutCorrection
    {
        public string Id { get; set; }
        public string ElementId { get; set; }
        public string CorrectionType { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();
        public string Description { get; set; }
    }

    /// <summary>
    /// Layout history entry
    /// </summary>
    public class LayoutHistoryEntry
    {
        public string Id { get; set; }
        public string CorrelationId { get; set; }
        public DateTime Timestamp { get; set; }
        public string Action { get; set; }
        public string Description { get; set; }
        public List<string> ElementIds { get; set; } = new List<string>();
        public bool CanRollback { get; set; }
    }
}
