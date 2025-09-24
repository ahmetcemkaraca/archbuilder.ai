using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using ArchBuilder.Desktop.Services;

namespace ArchBuilder.Desktop.ViewModels
{
    // Türkçe: Basit AI komut çağrısı ve sonuç gösterimi
    public class AICommandViewModel : INotifyPropertyChanged
    {
        private readonly ApiClient _api;
        private string _command = "";
        private string _inputJson = "{}";
        private string _result = "";
        private bool _busy;

        public string Command
        {
            get => _command;
            set { _command = value; OnPropertyChanged(); }
        }

        public string InputJson
        {
            get => _inputJson;
            set { _inputJson = value; OnPropertyChanged(); }
        }

        public string Result
        {
            get => _result;
            set { _result = value; OnPropertyChanged(); }
        }

        public bool Busy
        {
            get => _busy;
            set { _busy = value; OnPropertyChanged(); }
        }

        public AICommandViewModel(ApiClient api)
        {
            _api = api;
        }

        public async Task SendAsync()
        {
            if (string.IsNullOrWhiteSpace(Command)) return;
            Busy = true;
            try
            {
                var payload = new { command = Command, input = System.Text.Json.JsonSerializer.Deserialize<object>(InputJson) };
                var res = await _api.PostAsync<object, StandardEnvelope>("/v1/ai/commands", payload);
                Result = System.Text.Json.JsonSerializer.Serialize(res, new System.Text.Json.JsonSerializerOptions { WriteIndented = true });
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

    public class StandardEnvelope
    {
        public bool success { get; set; }
        public object? data { get; set; }
    }
}


