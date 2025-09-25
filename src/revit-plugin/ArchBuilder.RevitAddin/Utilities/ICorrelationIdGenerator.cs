using System;

namespace ArchBuilder.RevitAddin.Utilities
{
    /// <summary>
    /// Interface for generating correlation IDs for tracking operations
    /// </summary>
    public interface ICorrelationIdGenerator
    {
        /// <summary>
        /// Generate a new correlation ID
        /// </summary>
        /// <returns>Unique correlation ID</returns>
        string GenerateCorrelationId();

        /// <summary>
        /// Generate a correlation ID with prefix
        /// </summary>
        /// <param name="prefix">Prefix for the correlation ID</param>
        /// <returns>Unique correlation ID with prefix</returns>
        string GenerateCorrelationId(string prefix);

        /// <summary>
        /// Validate if a string is a valid correlation ID format
        /// </summary>
        /// <param name="correlationId">Correlation ID to validate</param>
        /// <returns>True if valid format</returns>
        bool IsValidCorrelationId(string correlationId);
    }
}
