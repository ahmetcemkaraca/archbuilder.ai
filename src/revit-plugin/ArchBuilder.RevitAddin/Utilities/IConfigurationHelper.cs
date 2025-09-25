using Microsoft.Extensions.Configuration;

namespace ArchBuilder.RevitAddin.Utilities
{
    /// <summary>
    /// Interface for configuration helper utilities
    /// </summary>
    public interface IConfigurationHelper
    {
        /// <summary>
        /// Get configuration value as string
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        string GetString(string key, string defaultValue = null);

        /// <summary>
        /// Get configuration value as integer
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        int GetInt(string key, int defaultValue = 0);

        /// <summary>
        /// Get configuration value as double
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        double GetDouble(string key, double defaultValue = 0.0);

        /// <summary>
        /// Get configuration value as boolean
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <param name="defaultValue">Default value if key not found</param>
        /// <returns>Configuration value or default</returns>
        bool GetBool(string key, bool defaultValue = false);

        /// <summary>
        /// Get configuration section
        /// </summary>
        /// <param name="key">Section key</param>
        /// <returns>Configuration section</returns>
        IConfigurationSection GetSection(string key);

        /// <summary>
        /// Check if configuration key exists
        /// </summary>
        /// <param name="key">Configuration key</param>
        /// <returns>True if key exists</returns>
        bool HasKey(string key);
    }
}
