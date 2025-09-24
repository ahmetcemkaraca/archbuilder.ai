using System.Windows;
using Microsoft.Win32;
using ArchBuilder.Desktop.Services;
using ArchBuilder.Desktop.ViewModels;

namespace ArchBuilder.Desktop.Views
{
    public partial class FileUploadWindow : Window
    {
        private readonly FileUploadViewModel _vm;
        public FileUploadWindow(ApiClient api)
        {
            InitializeComponent();
            _vm = new FileUploadViewModel(new DocumentService(api));
            DataContext = _vm;
        }

        private void OnBrowse(object sender, RoutedEventArgs e)
        {
            var dlg = new OpenFileDialog();
            if (dlg.ShowDialog() == true) _vm.FilePath = dlg.FileName;
        }

        private async void OnUpload(object sender, RoutedEventArgs e)
        {
            await _vm.UploadAsync();
        }

        private void OnClose(object sender, RoutedEventArgs e)
        {
            Close();
        }
    }
}


