using System.Windows;
using ArchBuilder.Desktop.Services;
using ArchBuilder.Desktop.ViewModels;

namespace ArchBuilder.Desktop.Views
{
    public partial class ProjectsWindow : Window
    {
        private readonly ProjectsViewModel _vm;
        public ProjectsWindow()
        {
            InitializeComponent();
            _vm = new ProjectsViewModel(new LocalProjectsService());
            DataContext = _vm;
        }

        private void OnCreate(object sender, RoutedEventArgs e)
        {
            _vm.Create();
        }
    }
}


