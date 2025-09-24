using System;
using System.Windows;
using ArchBuilder.Desktop.Services;
using ArchBuilder.Desktop.ViewModels;

namespace ArchBuilder.Desktop.Views
{
    public partial class MainWindow : Window
    {
        private readonly MainViewModel _vm;
        private readonly ApiClient _api;

        public MainWindow()
        {
            InitializeComponent();
            // Türkçe: Basit DI — ayarları okuyup istemci oluştur
            var settings = SettingsService.Load();
            _api = new ApiClient(settings.ApiBaseUrl) { ApiKey = settings.ApiKey };
            _vm = new MainViewModel(_api);
            DataContext = _vm;
        }

        private async void OnCheckHealth(object sender, RoutedEventArgs e)
        {
            await _vm.CheckHealthAsync();
        }

        private void OnOpenSettings(object sender, RoutedEventArgs e)
        {
            var dlg = new SettingsWindow();
            dlg.Owner = this;
            dlg.ShowDialog();
            // Türkçe: Ayarlar değişmişse ApiClient’ı güncelle
            var s = SettingsService.Load();
            _api.BearerToken = null;
            _api.ApiKey = s.ApiKey;
        }

        private async void OnLogin(object sender, RoutedEventArgs e)
        {
            var dlg = new LoginWindow { Owner = this };
            if (dlg.ShowDialog() == true && dlg.Tokens != null)
            {
                _api.BearerToken = dlg.Tokens.AccessToken;
                await _vm.CheckHealthAsync();
            }
        }

        private void OnLogout(object sender, RoutedEventArgs e)
        {
            _api.BearerToken = null;
        }

        private void OnOpenProjects(object sender, RoutedEventArgs e)
        {
            var w = new ProjectsWindow { Owner = this };
            w.ShowDialog();
        }

        private void OnOpenUpload(object sender, RoutedEventArgs e)
        {
            var w = new FileUploadWindow(_api) { Owner = this };
            w.ShowDialog();
        }

        private void OnOpenAI(object sender, RoutedEventArgs e)
        {
            var w = new AICommandWindow(_api) { Owner = this };
            w.ShowDialog();
        }
    }
}


