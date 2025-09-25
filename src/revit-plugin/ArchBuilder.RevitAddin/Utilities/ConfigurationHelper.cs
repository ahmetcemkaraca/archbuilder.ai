using Microsoft.Extensions.Configuration;
using System;

namespace ArchBuilder.RevitAddin.Utilities
{
    /// <summary>
    /// Configuration helper for accessing application settings
    /// </summary>
    public class ConfigurationHelper : IConfigurationHelper
    {
        private readonly IConfiguration _configuration;

        public ConfigurationHelper(IConfiguration configuration)
        {
            _configuration = configuration ?? throw new ArgumentNullException(nameof(configuration));
        }

        /// <summary>
        /// Get configuration value as string
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        public string GetString(string key, string defaultValue = null)
        {
            if (string.IsNullOrEmpty(key))
                return defaultValue;

            return _configuration[key] ?? defaultValue;
        }

        /// <summary>
        /// Get configuration value as integer
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        public int GetInt(string key, int defaultValue = 0)
        {
            if (string.IsNullOrEmpty(key))
                return defaultValue;

            var value = _configuration[key];
            if (string.IsNullOrEmpty(value))
                return defaultValue;

            return int.TryParse(value, out int result) ? result : defaultValue;
        }

        /// <summary>
        /// Get configuration value as double
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        public double GetDouble(string key, double defaultValue = 0.0)
        {
            if (string.IsNullOrEmpty(key))
                return defaultValue;

            var value = _configuration[key];
            if (string.IsNullOrEmpty(value))
                return defaultValue;

            return double.TryParse(value, out double result) ? result : defaultValue;
        }

        /// <summary>
        /// Get configuration value as boolean
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        public bool GetBool(string key, bool defaultValue = false)
        {
            if (string.IsNullOrEmpty(key))
                return defaultValue;

            var value = _configuration[key];
            if (string.IsNullOrEmpty(value))
                return defaultValue;

            return bool.TryParse(value, out bool result) ? result : defaultValue;
        }

        /// <summary>
        /// Get configuration section
        /// </summary>
        /// <param name="key">Section key</param>
        /// <returns>Configuration section</returns>
        public IConfigurationSection GetSection(string key)
        {
            if (string.IsNullOrEmpty(key))
                return null;

            return _configuration.GetSection(key);
        }

        /// <summary>
        /// Check if configuration key exists
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <returns>True if key exists</returns>
        public bool HasKey(string key)
        {
            if (string.IsNullOrEmpty(key))
                return false;

            return _configuration[key] != null;
        }
    }
}
