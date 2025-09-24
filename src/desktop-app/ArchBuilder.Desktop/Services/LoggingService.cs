using System;
using System.IO;
using Serilog;

namespace ArchBuilder.Desktop.Services
{
    // Türkçe: Uygulama-genel Serilog yapılandırması; dosyaya günlük yazar
    public static class LoggingService
    {
        private static bool _initialized;

        public static void EnsureInitialized()
        {
            if (_initialized) return;

            var logsDir = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
            Directory.CreateDirectory(logsDir);

            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Information()
                .Enrich.WithProperty("app", "ArchBuilder.Desktop")
                .WriteTo.File(Path.Combine(logsDir, "desktop-.log"), rollingInterval: RollingInterval.Day)
                .CreateLogger();

            _initialized = true;
            Log.Information("Serilog başlatıldı");
        }

        public static void Shutdown()
        {
            try
            {
                Log.Information("Serilog kapanıyor");
                Log.CloseAndFlush();
            }
            catch { /* yut */ }
        }
    }
}


