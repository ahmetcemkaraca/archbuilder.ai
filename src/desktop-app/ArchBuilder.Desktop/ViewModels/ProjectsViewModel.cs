using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using ArchBuilder.Desktop.Services;

namespace ArchBuilder.Desktop.ViewModels
{
    // Türkçe: Projeleri listeler ve yeni proje ekler
    public class ProjectsViewModel : INotifyPropertyChanged
    {
        private readonly LocalProjectsService _service;
        private string _newName = "";
        private string _newDescription = "";

        public ObservableCollection<ProjectItem> Items { get; } = new();

        public string NewName
        {
            get => _newName;
            set { _newName = value; OnPropertyChanged(); }
        }

        public string NewDescription
        {
            get => _newDescription;
            set { _newDescription = value; OnPropertyChanged(); }
        }

        public ProjectsViewModel(LocalProjectsService service)
        {
            _service = service;
            Load();
        }

        public void Load()
        {
            Items.Clear();
            foreach (var p in _service.GetAll()) Items.Add(p);
        }

        public void Create()
        {
            if (string.IsNullOrWhiteSpace(NewName)) return;
            var p = _service.Create(NewName, NewDescription);
            Items.Insert(0, p);
            NewName = "";
            NewDescription = "";
        }

        public event PropertyChangedEventHandler? PropertyChanged;
        private void OnPropertyChanged([CallerMemberName] string? name = null)
            => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
    }
}


