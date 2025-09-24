using System;
using System.Windows;
using ArchBuilder.Desktop.Services;
using Serilog;

namespace ArchBuilder.Desktop
{
    public partial class App : Application
    {
        // Türkçe: Uygulama başlatılırken logging kur ve kapanışta flush et
        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            LoggingService.EnsureInitialized();
            AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
        }

        protected override void OnExit(ExitEventArgs e)
        {
            base.OnExit(e);
            LoggingService.Shutdown();
        }

        private void OnUnhandledException(object sender, UnhandledExceptionEventArgs e)
        {
            try
            {
                Log.Error(e.ExceptionObject as Exception, "Yakalanmamış hata");
            }
            catch { }
        }
    }
}


