using System;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using ArchBuilder.Desktop.Services;

namespace ArchBuilder.Desktop.ViewModels
{
    // Türkçe: Dosya seçimi ve yükleme ilerlemesi
    public class FileUploadViewModel : INotifyPropertyChanged
    {
        private readonly DocumentService _docs;
        private string _filePath = "";
        private double _progress;
        private bool _busy;

        public string FilePath
        {
            get => _filePath;
            set { _filePath = value; OnPropertyChanged(); }
        }

        public double Progress
        {
            get => _progress;
            set { _progress = value; OnPropertyChanged(); }
        }

        public bool Busy
        {
            get => _busy;
            set { _busy = value; OnPropertyChanged(); }
        }

        public FileUploadViewModel(DocumentService docs)
        {
            _docs = docs;
        }

        public async Task UploadAsync()
        {
            if (string.IsNullOrWhiteSpace(FilePath)) return;
            Busy = true;
            try
            {
                var progress = new Progress<double>(v => Progress = v * 100);
                await _docs.UploadFileAsync(FilePath, progress);
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
}


