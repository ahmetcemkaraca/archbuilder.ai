using System.Windows;
using ArchBuilder.Desktop.Services;
using ArchBuilder.Desktop.ViewModels;

namespace ArchBuilder.Desktop.Views
{
    public partial class AICommandWindow : Window
    {
        private readonly AICommandViewModel _vm;
        public AICommandWindow(ApiClient api)
        {
            InitializeComponent();
            _vm = new AICommandViewModel(api);
            DataContext = _vm;
        }

        private async void OnSend(object sender, RoutedEventArgs e)
        {
            await _vm.SendAsync();
        }
    }
}


