using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Serilog;
using System;
using System.IO;

namespace ArchBuilder.RevitAddin.Configuration
{
    /// <summary>
    /// Configuration manager for ArchBuilder Revit Plugin
    /// Handles application configuration, logging setup, and dependency injection
    /// </summary>
    public static class ConfigurationManager
    {
        private static IHost _host;
        private static IConfiguration _configuration;
        private static ILogger<ConfigurationManager> _logger;

        /// <summary>
        /// Initialize configuration and logging for the Revit plugin
        /// </summary>
        public static void Initialize()
        {
            try
            {
                // Build configuration
                _configuration = new ConfigurationBuilder()
                    .SetBasePath(GetPluginDirectory())
                    .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true)
                    .AddEnvironmentVariables()
                    .Build();

                // Configure Serilog
                Log.Logger = new LoggerConfiguration()
                    .ReadFrom.Configuration(_configuration)
                    .Enrich.FromLogContext()
                    .Enrich.WithMachineName()
                    .Enrich.WithThreadId()
                    .CreateLogger();

                // Build host with dependency injection
                _host = Host.CreateDefaultBuilder()
                    .ConfigureServices(ConfigureServices)
                    .UseSerilog()
                    .Build();

                _logger = _host.Services.GetRequiredService<ILogger<ConfigurationManager>>();
                _logger.LogInformation("ArchBuilder Revit Plugin configuration initialized successfully");
            }
            catch (Exception ex)
            {
                // Fallback logging if configuration fails
                Log.Logger = new LoggerConfiguration()
                    .WriteTo.Console()
                    .WriteTo.Debug()
                    .CreateLogger();
                
                Log.Error(ex, "Failed to initialize ArchBuilder configuration");
                throw;
            }
        }

        /// <summary>
        /// Get the plugin directory path
        /// </summary>
        private static string GetPluginDirectory()
        {
            var assemblyLocation = System.Reflection.Assembly.GetExecutingAssembly().Location;
            return Path.GetDirectoryName(assemblyLocation);
        }

        /// <summary>
        /// Configure dependency injection services
        /// </summary>
        private static void ConfigureServices(IServiceCollection services)
        {
            // Configuration
            services.AddSingleton(_configuration);

            // Logging
            services.AddLogging(builder =>
            {
                builder.AddSerilog();
            });

            // HTTP Client
            services.AddHttpClient("ArchBuilderAPI", client =>
            {
                var baseUrl = _configuration["ArchBuilder:ApiBaseUrl"];
                var timeout = _configuration.GetValue<int>("ArchBuilder:TimeoutSeconds");
                
                client.BaseAddress = new Uri(baseUrl);
                client.Timeout = TimeSpan.FromSeconds(timeout);
                client.DefaultRequestHeaders.Add("User-Agent", "ArchBuilder-Revit-Plugin/1.0");
            });

            // Services
            services.AddSingleton<Services.ILayoutService, Services.LayoutService>();
            services.AddSingleton<Services.IProjectAnalysisService, Services.ProjectAnalysisService>();
            services.AddSingleton<Services.ILocalCommunicationService, Services.LocalCommunicationService>();
            services.AddSingleton<Services.ITransactionService, Services.TransactionService>();
            services.AddSingleton<Services.IValidationService, Services.ValidationService>();

            // Utilities
            services.AddSingleton<Utilities.ICorrelationIdGenerator, Utilities.CorrelationIdGenerator>();
            services.AddSingleton<Utilities.IConfigurationHelper, Utilities.ConfigurationHelper>();
        }

        /// <summary>
        /// Get service from dependency injection container
        /// </summary>
        public static T GetService<T>() where T : class
        {
            if (_host == null)
            {
                throw new InvalidOperationException("Configuration not initialized. Call Initialize() first.");
            }
            
            return _host.Services.GetRequiredService<T>();
        }

        /// <summary>
        /// Get configuration value
        /// </summary>
        public static string GetConfigurationValue(string key)
        {
            return _configuration?[key];
        }

        /// <summary>
        /// Get configuration section
        /// </summary>
        public static IConfigurationSection GetConfigurationSection(string key)
        {
            return _configuration?.GetSection(key);
        }

        /// <summary>
        /// Dispose resources
        /// </summary>
        public static void Dispose()
        {
            try
            {
                _host?.Dispose();
                Log.CloseAndFlush();
            }
            catch (Exception ex)
            {
                // Log error but don't throw during disposal
                Console.WriteLine($"Error during disposal: {ex.Message}");
            }
        }
    }
}
