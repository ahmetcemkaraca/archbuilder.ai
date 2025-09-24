using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;

namespace ArchBuilder.Desktop.Services
{
    // Türkçe: Yerel proje listesi JSON dosyasında saklanır
    public class LocalProjectsService
    {
        private const string FileName = "projects.json";

        public List<ProjectItem> GetAll()
        {
            var path = GetPath();
            if (!File.Exists(path)) return new List<ProjectItem>();
            var json = File.ReadAllText(path);
            return JsonSerializer.Deserialize<List<ProjectItem>>(json) ?? new List<ProjectItem>();
        }

        public ProjectItem Create(string name, string? description = null)
        {
            var items = GetAll();
            var item = new ProjectItem
            {
                Id = Guid.NewGuid().ToString(),
                Name = name,
                Description = description ?? string.Empty,
                CreatedAtUtc = DateTime.UtcNow
            };
            items.Add(item);
            Save(items);
            return item;
        }

        public void Save(List<ProjectItem> items)
        {
            var json = JsonSerializer.Serialize(items.OrderByDescending(i => i.CreatedAtUtc).ToList(), new JsonSerializerOptions { WriteIndented = true });
            Directory.CreateDirectory(Path.GetDirectoryName(GetPath())!);
            File.WriteAllText(GetPath(), json);
        }

        private static string GetPath()
        {
            var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ArchBuilder.Desktop");
            return Path.Combine(dir, FileName);
        }
    }

    public class ProjectItem
    {
        public string Id { get; set; } = string.Empty;
        public string Name { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
        public DateTime CreatedAtUtc { get; set; }
    }
}


