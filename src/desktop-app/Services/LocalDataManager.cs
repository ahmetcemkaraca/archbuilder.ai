using System;
using System.IO;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using ArchBuilder.Desktop.Models;
using ArchBuilder.Desktop.Interfaces;

namespace ArchBuilder.Desktop.Services
{
    /// <summary>
    /// Revit verilerini lokal JSON formatında saklama ve yönetme servisi
    /// </summary>
    public class LocalDataManager : ILocalDataManager
    {
        private readonly ILogger<LocalDataManager> _logger;
        private readonly IConfiguration _configuration;
        private readonly string _localDataPath;
        private readonly string _backupPath;
        
        // JSON serialization options
        private readonly JsonSerializerOptions _jsonOptions = new()
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull,
            Encoder = System.Text.Encodings.Web.JavaScriptEncoder.UnsafeRelaxedJsonEscaping
        };

        public LocalDataManager(
            ILogger<LocalDataManager> logger,
            IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            
            // Lokal veri yollarını yapılandır
            var appDataPath = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);
            _localDataPath = Path.Combine(appDataPath, "ArchBuilder.AI", "RevitData");
            _backupPath = Path.Combine(appDataPath, "ArchBuilder.AI", "Backups");
            
            // Klasörleri oluştur
            EnsureDirectoriesExist();
            
            _logger.LogInformation("LocalDataManager başlatıldı", 
                new { LocalDataPath = _localDataPath, BackupPath = _backupPath });
        }

        /// <summary>
        /// Revit model verilerini JSON formatında lokal olarak kaydet
        /// </summary>
        public async Task<LocalDataResult> SaveRevitDataAsync(RevitModelData modelData)
        {
            var correlationId = Guid.NewGuid().ToString();
            
            try
            {
                _logger.LogInformation("Revit veri kaydı başladı",
                    new { CorrelationId = correlationId, ModelId = modelData.Id });

                // Dosya adı ve yol oluştur
                var timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
                var filename = $"{modelData.ProjectName}_{timestamp}_{correlationId[..8]}.json";
                var filePath = Path.Combine(_localDataPath, filename);

                // Veri bütünlüğü kontrolü için hash hesapla
                var dataHash = CalculateDataHash(modelData);
                
                // Metadata ekle
                var wrappedData = new LocalRevitData
                {
                    CorrelationId = correlationId,
                    SavedAt = DateTime.UtcNow,
                    ProjectName = modelData.ProjectName,
                    RevitVersion = modelData.RevitVersion,
                    DataHash = dataHash,
                    CompressionUsed = false,
                    ModelData = modelData
                };

                // JSON olarak serialize et
                var jsonData = JsonSerializer.Serialize(wrappedData, _jsonOptions);
                
                // Dosyaya yaz
                await File.WriteAllTextAsync(filePath, jsonData, Encoding.UTF8);
                
                // Backup oluştur
                await CreateBackupAsync(filePath, correlationId);

                var result = new LocalDataResult
                {
                    Success = true,
                    CorrelationId = correlationId,
                    FilePath = filePath,
                    DataHash = dataHash,
                    SizeBytes = new FileInfo(filePath).Length,
                    Message = "Veri başarıyla kaydedildi"
                };

                _logger.LogInformation("Revit veri kaydı tamamlandı",
                    new { CorrelationId = correlationId, FilePath = filePath, SizeBytes = result.SizeBytes });

                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Revit veri kaydı hatası",
                    new { CorrelationId = correlationId, ProjectName = modelData.ProjectName });

                return new LocalDataResult
                {
                    Success = false,
                    CorrelationId = correlationId,
                    Message = $"Veri kaydetme hatası: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Verileri sıkıştırarak kaydet (bulut gönderimi öncesi)
        /// </summary>
        public async Task<LocalDataResult> SaveCompressedDataAsync(string sourceFilePath, bool deleteSource = false)
        {
            var correlationId = Guid.NewGuid().ToString();
            
            try
            {
                if (!File.Exists(sourceFilePath))
                    throw new FileNotFoundException($"Kaynak dosya bulunamadı: {sourceFilePath}");

                var sourceInfo = new FileInfo(sourceFilePath);
                var compressedFileName = Path.GetFileNameWithoutExtension(sourceFilePath) + "_compressed.gz";
                var compressedPath = Path.Combine(_localDataPath, "Compressed", compressedFileName);
                
                // Compressed klasörünü oluştur
                Directory.CreateDirectory(Path.GetDirectoryName(compressedPath)!);

                _logger.LogInformation("Veri sıkıştırma başladı",
                    new { CorrelationId = correlationId, SourceFile = sourceFilePath });

                // Dosyayı sıkıştır
                using (var sourceStream = File.OpenRead(sourceFilePath))
                using (var compressedStream = File.Create(compressedPath))
                using (var gzipStream = new GZipStream(compressedStream, CompressionLevel.Optimal))
                {
                    await sourceStream.CopyToAsync(gzipStream);
                }

                var compressedInfo = new FileInfo(compressedPath);
                var compressionRatio = (double)compressedInfo.Length / sourceInfo.Length;

                _logger.LogInformation("Veri sıkıştırma tamamlandı",
                    new { 
                        CorrelationId = correlationId,
                        OriginalSize = sourceInfo.Length,
                        CompressedSize = compressedInfo.Length,
                        CompressionRatio = compressionRatio
                    });

                // Orijinal dosyayı sil (istenirse)
                if (deleteSource)
                {
                    File.Delete(sourceFilePath);
                    _logger.LogInformation("Orijinal dosya silindi", new { SourceFile = sourceFilePath });
                }

                return new LocalDataResult
                {
                    Success = true,
                    CorrelationId = correlationId,
                    FilePath = compressedPath,
                    SizeBytes = compressedInfo.Length,
                    OriginalSizeBytes = sourceInfo.Length,
                    CompressionRatio = compressionRatio,
                    Message = $"Veri sıkıştırıldı (%{(1 - compressionRatio) * 100:F1} tasarruf)"
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Veri sıkıştırma hatası",
                    new { CorrelationId = correlationId, SourceFile = sourceFilePath });

                return new LocalDataResult
                {
                    Success = false,
                    CorrelationId = correlationId,
                    Message = $"Sıkıştırma hatası: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Sıkıştırılmış veriyi açarak oku
        /// </summary>
        public async Task<T> ReadCompressedDataAsync<T>(string compressedFilePath) where T : class
        {
            try
            {
                if (!File.Exists(compressedFilePath))
                    throw new FileNotFoundException($"Sıkıştırılmış dosya bulunamadı: {compressedFilePath}");

                _logger.LogInformation("Sıkıştırılmış veri okunuyor", new { FilePath = compressedFilePath });

                using var compressedStream = File.OpenRead(compressedFilePath);
                using var gzipStream = new GZipStream(compressedStream, CompressionMode.Decompress);
                using var reader = new StreamReader(gzipStream, Encoding.UTF8);
                
                var jsonData = await reader.ReadToEndAsync();
                var data = JsonSerializer.Deserialize<T>(jsonData, _jsonOptions);

                _logger.LogInformation("Sıkıştırılmış veri başarıyla okundu", new { FilePath = compressedFilePath });
                
                return data ?? throw new InvalidOperationException("Deserialization null döndü");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Sıkıştırılmış veri okuma hatası", new { FilePath = compressedFilePath });
                throw;
            }
        }

        /// <summary>
        /// Lokal olarak kaydedilmiş veriyi oku
        /// </summary>
        public async Task<T> ReadLocalDataAsync<T>(string correlationId) where T : class
        {
            try
            {
                var files = Directory.GetFiles(_localDataPath, $"*{correlationId[..8]}*.json");
                
                if (files.Length == 0)
                    throw new FileNotFoundException($"CorrelationId ile eşleşen dosya bulunamadı: {correlationId}");

                var filePath = files[0]; // İlk eşleşeni al
                
                _logger.LogInformation("Lokal veri okunuyor", new { CorrelationId = correlationId, FilePath = filePath });

                var jsonData = await File.ReadAllTextAsync(filePath, Encoding.UTF8);
                var data = JsonSerializer.Deserialize<T>(jsonData, _jsonOptions);

                _logger.LogInformation("Lokal veri başarıyla okundu", new { CorrelationId = correlationId });
                
                return data ?? throw new InvalidOperationException("Deserialization null döndü");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Lokal veri okuma hatası", new { CorrelationId = correlationId });
                throw;
            }
        }

        /// <summary>
        /// Veri bütünlüğü doğrulaması
        /// </summary>
        public async Task<bool> ValidateDataIntegrityAsync(string filePath, string expectedHash)
        {
            try
            {
                if (!File.Exists(filePath))
                    return false;

                var data = await ReadLocalDataAsync<LocalRevitData>(Path.GetFileNameWithoutExtension(filePath));
                if (data?.ModelData == null)
                    return false;

                var currentHash = CalculateDataHash(data.ModelData);
                var isValid = currentHash.Equals(expectedHash, StringComparison.OrdinalIgnoreCase);

                _logger.LogInformation("Veri bütünlüğü kontrolü",
                    new { FilePath = filePath, IsValid = isValid, ExpectedHash = expectedHash, CurrentHash = currentHash });

                return isValid;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Veri bütünlüğü kontrolü hatası", new { FilePath = filePath });
                return false;
            }
        }

        /// <summary>
        /// Lokal veri dosyalarını listele
        /// </summary>
        public Task<List<LocalDataInfo>> ListLocalDataAsync()
        {
            try
            {
                var dataFiles = new List<LocalDataInfo>();
                var files = Directory.GetFiles(_localDataPath, "*.json");

                foreach (var file in files)
                {
                    var info = new FileInfo(file);
                    dataFiles.Add(new LocalDataInfo
                    {
                        FilePath = file,
                        FileName = info.Name,
                        SizeBytes = info.Length,
                        CreatedAt = info.CreationTime,
                        LastModified = info.LastWriteTime
                    });
                }

                _logger.LogInformation("Lokal veri dosyaları listelendi", new { FileCount = dataFiles.Count });
                
                return Task.FromResult(dataFiles);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Lokal veri listeleme hatası");
                return Task.FromResult(new List<LocalDataInfo>());
            }
        }

        /// <summary>
        /// Temizlik işlemleri (eski dosyaları sil)
        /// </summary>
        public async Task<int> CleanupOldDataAsync(TimeSpan olderThan)
        {
            try
            {
                var cutoffDate = DateTime.Now - olderThan;
                var files = Directory.GetFiles(_localDataPath, "*.json");
                var deletedCount = 0;

                foreach (var file in files)
                {
                    var info = new FileInfo(file);
                    if (info.CreationTime < cutoffDate)
                    {
                        File.Delete(file);
                        deletedCount++;
                        _logger.LogInformation("Eski veri dosyası silindi", new { FilePath = file, CreatedAt = info.CreationTime });
                    }
                }

                _logger.LogInformation("Temizlik işlemi tamamlandı", new { DeletedFileCount = deletedCount });
                
                return deletedCount;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Temizlik işlemi hatası");
                return 0;
            }
        }

        #region Private Methods

        private void EnsureDirectoriesExist()
        {
            Directory.CreateDirectory(_localDataPath);
            Directory.CreateDirectory(_backupPath);
            Directory.CreateDirectory(Path.Combine(_localDataPath, "Compressed"));
        }

        private string CalculateDataHash(object data)
        {
            var jsonData = JsonSerializer.Serialize(data, _jsonOptions);
            var bytes = Encoding.UTF8.GetBytes(jsonData);
            
            using var sha256 = SHA256.Create();
            var hashBytes = sha256.ComputeHash(bytes);
            return Convert.ToBase64String(hashBytes);
        }

        private async Task CreateBackupAsync(string sourceFilePath, string correlationId)
        {
            try
            {
                var backupFileName = $"backup_{correlationId[..8]}_{DateTime.Now:yyyyMMdd_HHmmss}.json";
                var backupFilePath = Path.Combine(_backupPath, backupFileName);
                
                await File.CopyAsync(sourceFilePath, backupFilePath);
                
                _logger.LogInformation("Backup oluşturuldu", new { SourceFile = sourceFilePath, BackupFile = backupFilePath });
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Backup oluşturma hatası", new { SourceFile = sourceFilePath });
                // Backup hatası ana işlemi engellemez
            }
        }

        #endregion
    }
}