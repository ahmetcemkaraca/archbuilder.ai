using System;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace ArchBuilder.Desktop.Services
{
    // Türkçe: Kullanıcı-özel güvenli ayar saklama (DPAPI)
    public static class SettingsService
    {
        private const string FileName = "user.settings.json.enc";

        public static AppSettings Load()
        {
            var path = GetPath();
            if (!File.Exists(path))
            {
                return new AppSettings
                {
                    ApiBaseUrl = "https://api.archbuilder.app/v1",
                    ApiKey = string.Empty
                };
            }

            var encrypted = File.ReadAllBytes(path);
            var data = ProtectedData.Unprotect(encrypted, null, DataProtectionScope.CurrentUser);
            var json = Encoding.UTF8.GetString(data);
            return JsonSerializer.Deserialize<AppSettings>(json)!;
        }

        public static void Save(AppSettings settings)
        {
            var json = JsonSerializer.Serialize(settings, new JsonSerializerOptions { WriteIndented = true });
            var bytes = Encoding.UTF8.GetBytes(json);
            var encrypted = ProtectedData.Protect(bytes, null, DataProtectionScope.CurrentUser);
            Directory.CreateDirectory(Path.GetDirectoryName(GetPath())!);
            File.WriteAllBytes(GetPath(), encrypted);
        }

        private static string GetPath()
        {
            var dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "ArchBuilder.Desktop");
            return Path.Combine(dir, FileName);
        }
    }

    public class AppSettings
    {
        public string ApiBaseUrl { get; set; } = string.Empty; // Türkçe: API ana URL
        public string ApiKey { get; set; } = string.Empty;     // Türkçe: Kullanıcı API anahtarı
    }
}


