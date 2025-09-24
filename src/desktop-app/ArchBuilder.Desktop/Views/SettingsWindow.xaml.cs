using System.Windows;
using ArchBuilder.Desktop.Services;
using ArchBuilder.Desktop.ViewModels;

namespace ArchBuilder.Desktop.Views
{
    public partial class SettingsWindow : Window
    {
        private readonly SettingsViewModel _vm;

        public SettingsWindow()
        {
            InitializeComponent();
            var settings = SettingsService.Load();
            _vm = new SettingsViewModel
            {
                ApiBaseUrl = settings.ApiBaseUrl,
                ApiKey = settings.ApiKey
            };
            DataContext = _vm;
            ApiKeyBox.Password = _vm.ApiKey;
        }

        private void OnPasswordChanged(object sender, RoutedEventArgs e)
        {
            _vm.ApiKey = ApiKeyBox.Password;
        }

        private void OnSave(object sender, RoutedEventArgs e)
        {
            SettingsService.Save(new AppSettings
            {
                ApiBaseUrl = _vm.ApiBaseUrl,
                ApiKey = _vm.ApiKey
            });
            Close();
        }

        private void OnClose(object sender, RoutedEventArgs e)
        {
            Close();
        }
    }
}


