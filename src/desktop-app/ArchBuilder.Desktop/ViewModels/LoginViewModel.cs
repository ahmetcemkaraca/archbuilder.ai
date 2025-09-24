using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace ArchBuilder.Desktop.ViewModels
{
    // Türkçe: Login ekranı için VM — basit doğrulama ve hata alanı
    public class LoginViewModel : INotifyPropertyChanged
    {
        private string _email = "";
        private string _password = "";
        private string _error = "";

        public string Email
        {
            get => _email;
            set { _email = value; OnPropertyChanged(); }
        }

        public string Password
        {
            get => _password;
            set { _password = value; OnPropertyChanged(); }
        }

        public string Error
        {
            get => _error;
            set { _error = value; OnPropertyChanged(); }
        }

        public bool IsValid()
        {
            if (string.IsNullOrWhiteSpace(Email)) { Error = "Email gerekli"; return false; }
            if (string.IsNullOrWhiteSpace(Password)) { Error = "Şifre gerekli"; return false; }
            Error = string.Empty; return true;
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        private void OnPropertyChanged([CallerMemberName] string? name = null)
            => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}


