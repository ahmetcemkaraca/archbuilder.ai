using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using ArchBuilder.Desktop.Services;
using Serilog;

namespace ArchBuilder.Desktop.ViewModels
{
    // Türkçe: Ana ekran için basit VM — /health kontrolünü yapar
    public class MainViewModel : INotifyPropertyChanged
    {
        private readonly ApiClient _api;
        private string _status = "";
        private bool _busy;

        public string Status
        {
            get => _status;
            set { _status = value; OnPropertyChanged(); }
        }

        public bool Busy
        {
            get => _busy;
            set { _busy = value; OnPropertyChanged(); }
        }

        public MainViewModel(ApiClient api)
        {
            _api = api;
        }

        public async Task CheckHealthAsync()
        {
            try
            {
                Busy = true;
                var res = await _api.GetAsync<HealthResponse>("/health");
                Status = $"{res.name}: {res.status}";
            }
            catch (Exception ex)
            {
                Log.Warning(ex, "Sağlık kontrolü başarısız");
                Status = "Error";
            }
            finally
            {
                Busy = false;
            }
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        private void OnPropertyChanged([CallerMemberName] string? name = null)
            => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }

    public class HealthResponse
    {
        public string status { get; set; } = "";
        public string name { get; set; } = "";
    }
}


