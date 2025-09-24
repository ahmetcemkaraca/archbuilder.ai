using System;
using System.Threading.Tasks;
using System.Windows;
using ArchBuilder.Desktop.Services;
using ArchBuilder.Desktop.ViewModels;
using Serilog;

namespace ArchBuilder.Desktop.Views
{
    public partial class LoginWindow : Window
    {
        private readonly LoginViewModel _vm;
        private readonly AuthService _auth;
        private readonly ApiClient _api;

        public AuthTokens? Tokens { get; private set; }

        public LoginWindow()
        {
            InitializeComponent();
            var settings = SettingsService.Load();
            _api = new ApiClient(settings.ApiBaseUrl) { ApiKey = settings.ApiKey };
            _auth = new AuthService(_api);
            _vm = new LoginViewModel();
            DataContext = _vm;
        }

        private void OnPasswordChanged(object sender, RoutedEventArgs e)
        {
            _vm.Password = PasswordBox.Password;
        }

        private async void OnLogin(object sender, RoutedEventArgs e)
        {
            if (!_vm.IsValid()) return;
            try
            {
                var tokens = await _auth.LoginAsync(_vm.Email, _vm.Password);
                Tokens = tokens;
                DialogResult = true;
                Close();
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Login hatası");
                _vm.Error = "Giriş başarısız. Bilgileri kontrol edin.";
            }
        }

        private void OnCancel(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}


