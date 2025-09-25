using System;
using System.Security.Cryptography;
using System.Text;

namespace ArchBuilder.RevitAddin.Utilities
{
    /// <summary>
    /// Generates correlation IDs for tracking operations across services
    /// </summary>
    public class CorrelationIdGenerator : ICorrelationIdGenerator
    {
        private const string CORRELATION_ID_PATTERN = "^[A-Z]{2,3}_\\d{14}_[a-f0-9]{32}$";
        private static readonly Random _random = new Random();

        /// <summary>
        /// Generate a new correlation ID with default prefix
        /// </summary>
        /// <returns>Unique correlation ID</returns>
        public string GenerateCorrelationId()
        {
            return GenerateCorrelationId("RVT");
        }

        /// <summary>
        /// Generate a correlation ID with specified prefix
        /// </summary>
        /// <param name="prefix">Prefix for the correlation ID (2-3 characters)</param>
        /// <returns>Unique correlation ID with prefix</returns>
        public string GenerateCorrelationId(string prefix)
        {
            if (string.IsNullOrEmpty(prefix))
                throw new ArgumentException("Prefix cannot be null or empty", nameof(prefix));

            if (prefix.Length < 2 || prefix.Length > 3)
                throw new ArgumentException("Prefix must be 2-3 characters long", nameof(prefix));

            // Format: PREFIX_YYYYMMDDHHMMSS_HASH
            var timestamp = DateTime.UtcNow.ToString("yyyyMMddHHmmss");
            var hash = GenerateHash(prefix + timestamp + Guid.NewGuid().ToString());
            
            return $"{prefix}_{timestamp}_{hash}";
        }

        /// <summary>
        /// Validate if a string is a valid correlation ID format
        /// </summary>
        /// <param name="correlationId">Correlation ID to validate</param>
        /// <returns>True if valid format</returns>
        public bool IsValidCorrelationId(string correlationId)
        {
            if (string.IsNullOrEmpty(correlationId))
                return false;

            return System.Text.RegularExpressions.Regex.IsMatch(correlationId, CORRELATION_ID_PATTERN);
        }

        /// <summary>
        /// Generate a hash for the correlation ID
        /// </summary>
        /// <param name="input">Input string to hash</param>
        /// <returns>32-character hexadecimal hash</returns>
        private string GenerateHash(string input)
        {
            using (var sha256 = SHA256.Create())
            {
                var hashBytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(input));
                return BitConverter.ToString(hashBytes).Replace("-", "").ToLowerInvariant();
            }
        }
    }
}
