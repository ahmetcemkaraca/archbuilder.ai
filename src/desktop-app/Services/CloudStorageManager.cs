using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using ArchBuilder.Desktop.Interfaces;
using ArchBuilder.Desktop.Models;

namespace ArchBuilder.Desktop.Services
{
    /// <summary>
    /// Cloud-agnostic storage manager - Provider değiştirilebilir
    /// </summary>
    public class CloudStorageManager : ICloudStorageManager
    {
        private readonly ILogger<CloudStorageManager> _logger;
        private readonly IConfiguration _configuration;
        private readonly ILocalDataManager _localDataManager;
        private readonly IUserPermissionService _permissionService;
        private readonly Dictionary<string, ICloudStorageProvider> _providers;
        
        private ICloudStorageProvider _activeProvider;
        private string _activeProviderName;

        public CloudStorageManager(
            ILogger<CloudStorageManager> logger,
            IConfiguration configuration,
            ILocalDataManager localDataManager,
            IUserPermissionService permissionService,
            IEnumerable<ICloudStorageProvider> providers)
        {
            _logger = logger;
            _configuration = configuration;
            _localDataManager = localDataManager;
            _permissionService = permissionService;
            
            // Provider'ları kaydet
            _providers = providers.ToDictionary(p => p.ProviderName, p => p);
            
            // Varsayılan provider'ı yükle
            _activeProviderName = _configuration.GetValue<string>("CloudStorage:DefaultProvider", "GoogleCloud");
            
            if (_providers.ContainsKey(_activeProviderName))
            {
                _activeProvider = _providers[_activeProviderName];
                _logger.LogInformation("Aktif cloud provider ayarlandı", new { Provider = _activeProviderName });
            }
            else
            {
                _logger.LogWarning("Varsayılan provider bulunamadı, ilk provider kullanılıyor", 
                    new { RequestedProvider = _activeProviderName });
                
                if (_providers.Any())
                {
                    _activeProvider = _providers.First().Value;
                    _activeProviderName = _activeProvider.ProviderName;
                }
            }
        }

        /// <summary>
        /// Kullanıcı izni kontrol et
        /// </summary>
        public async Task<bool> HasUserPermissionAsync()
        {
            try
            {
                var hasPermission = await _permissionService.HasCloudSyncPermissionAsync();
                
                _logger.LogInformation("Kullanıcı bulut sync izni kontrol edildi", new { HasPermission = hasPermission });
                
                return hasPermission;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Kullanıcı izni kontrolü hatası");
                return false;
            }
        }

        /// <summary>
        /// Kullanıcı izni iste
        /// </summary>
        public async Task<bool> RequestUserPermissionAsync()
        {
            try
            {
                _logger.LogInformation("Kullanıcıdan bulut sync izni isteniyor");
                
                var granted = await _permissionService.RequestCloudSyncPermissionAsync();
                
                if (granted)
                {
                    _logger.LogInformation("Kullanıcı bulut sync iznini verdi");
                }
                else
                {
                    _logger.LogInformation("Kullanıcı bulut sync iznini reddetti");
                }

                return granted;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Kullanıcı izni isteme hatası");
                return false;
            }
        }

        /// <summary>
        /// Lokal dosyayı sıkıştırıp buluta yükle
        /// </summary>
        public async Task<CloudSyncResult> SyncToCloudAsync(string localFilePath, SyncOptions options = null)
        {
            var correlationId = Guid.NewGuid().ToString();
            var startTime = DateTime.UtcNow;
            
            try
            {
                options ??= new SyncOptions();
                
                _logger.LogInformation("Bulut sync başladı",
                    new { CorrelationId = correlationId, LocalFile = localFilePath, Provider = _activeProviderName });

                // Kullanıcı izni kontrol et
                if (!await HasUserPermissionAsync())
                {
                    if (!await RequestUserPermissionAsync())
                    {
                        return new CloudSyncResult
                        {
                            Success = false,
                            CorrelationId = correlationId,
                            LocalPath = localFilePath,
                            Message = "Kullanıcı bulut sync iznini reddetti"
                        };
                    }
                }

                // Provider sağlık kontrolü
                if (!await _activeProvider.IsHealthyAsync())
                {
                    return new CloudSyncResult
                    {
                        Success = false,
                        CorrelationId = correlationId,
                        LocalPath = localFilePath,
                        Message = $"Cloud provider ({_activeProviderName}) sağlıklı değil"
                    };
                }

                string fileToUpload = localFilePath;
                bool needsCleanup = false;

                // Sıkıştırma (istenirse)
                if (options.CompressBeforeUpload)
                {
                    var compressionResult = await _localDataManager.SaveCompressedDataAsync(localFilePath);
                    
                    if (compressionResult.Success)
                    {
                        fileToUpload = compressionResult.FilePath;
                        needsCleanup = true;
                        
                        _logger.LogInformation("Dosya sıkıştırıldı",
                            new { CorrelationId = correlationId, CompressionRatio = compressionResult.CompressionRatio });
                    }
                    else
                    {
                        _logger.LogWarning("Sıkıştırma başarısız, orijinal dosya yüklenecek",
                            new { CorrelationId = correlationId, Error = compressionResult.Message });
                    }
                }

                // Remote path oluştur
                var fileName = Path.GetFileName(fileToUpload);
                var remotePath = $"revit-data/{DateTime.UtcNow:yyyy/MM/dd}/{correlationId}/{fileName}";

                // Upload seçenekleri hazırla
                var uploadOptions = new UploadOptions
                {
                    OverwriteExisting = true,
                    VerifyIntegrity = options.VerifyIntegrity,
                    Metadata = new Dictionary<string, string>
                    {
                        ["correlation-id"] = correlationId,
                        ["uploaded-at"] = DateTime.UtcNow.ToString("O"),
                        ["original-file"] = Path.GetFileName(localFilePath),
                        ["compressed"] = options.CompressBeforeUpload.ToString().ToLower()
                    }
                };

                // Tags ekle
                foreach (var tag in options.Tags)
                {
                    uploadOptions.Metadata[$"tag-{tag.Key}"] = tag.Value;
                }

                // Bulut yüklemesi
                var uploadResult = await _activeProvider.UploadFileAsync(fileToUpload, remotePath, uploadOptions);

                // Cleanup (gerekirse)
                if (needsCleanup && File.Exists(fileToUpload))
                {
                    File.Delete(fileToUpload);
                }

                // Lokal dosyayı sil (istenirse)
                if (uploadResult.Success && options.DeleteLocalAfterUpload)
                {
                    File.Delete(localFilePath);
                    _logger.LogInformation("Lokal dosya silindi", new { CorrelationId = correlationId, LocalFile = localFilePath });
                }

                var duration = DateTime.UtcNow - startTime;

                var result = new CloudSyncResult
                {
                    Success = uploadResult.Success,
                    CorrelationId = correlationId,
                    LocalPath = localFilePath,
                    RemotePath = uploadResult.Success ? remotePath : string.Empty,
                    Direction = SyncDirection.ToCloud,
                    SizeBytes = uploadResult.SizeBytes,
                    Duration = duration,
                    Message = uploadResult.Message,
                    DataIntegrityVerified = options.VerifyIntegrity
                };

                if (uploadResult.Success)
                {
                    _logger.LogInformation("Bulut sync tamamlandı",
                        new { CorrelationId = correlationId, RemotePath = remotePath, Duration = duration.TotalSeconds });
                }
                else
                {
                    _logger.LogError("Bulut sync başarısız",
                        new { CorrelationId = correlationId, Error = uploadResult.Message });
                }

                return result;
            }
            catch (Exception ex)
            {
                var duration = DateTime.UtcNow - startTime;
                
                _logger.LogError(ex, "Bulut sync hatası",
                    new { CorrelationId = correlationId, LocalFile = localFilePath });

                return new CloudSyncResult
                {
                    Success = false,
                    CorrelationId = correlationId,
                    LocalPath = localFilePath,
                    Direction = SyncDirection.ToCloud,
                    Duration = duration,
                    Message = $"Sync hatası: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Buluttan dosyayı indir ve lokal olarak açarak kaydet
        /// </summary>
        public async Task<CloudSyncResult> SyncFromCloudAsync(string remotePath, string localPath)
        {
            var correlationId = Guid.NewGuid().ToString();
            var startTime = DateTime.UtcNow;

            try
            {
                _logger.LogInformation("Buluttan sync başladı",
                    new { CorrelationId = correlationId, RemotePath = remotePath, LocalPath = localPath });

                // Provider sağlık kontrolü
                if (!await _activeProvider.IsHealthyAsync())
                {
                    return new CloudSyncResult
                    {
                        Success = false,
                        CorrelationId = correlationId,
                        RemotePath = remotePath,
                        Message = $"Cloud provider ({_activeProviderName}) sağlıklı değil"
                    };
                }

                // Dosya var mı kontrol et
                if (!await _activeProvider.FileExistsAsync(remotePath))
                {
                    return new CloudSyncResult
                    {
                        Success = false,
                        CorrelationId = correlationId,
                        RemotePath = remotePath,
                        Message = "Dosya bulutta bulunamadı"
                    };
                }

                // Download
                var downloadResult = await _activeProvider.DownloadFileAsync(remotePath, localPath);
                var duration = DateTime.UtcNow - startTime;

                var result = new CloudSyncResult
                {
                    Success = downloadResult.Success,
                    CorrelationId = correlationId,
                    LocalPath = downloadResult.LocalPath,
                    RemotePath = remotePath,
                    Direction = SyncDirection.FromCloud,
                    SizeBytes = downloadResult.SizeBytes,
                    Duration = duration,
                    Message = downloadResult.Message,
                    DataIntegrityVerified = true // Provider'ın ETag kontrolü ile
                };

                if (downloadResult.Success)
                {
                    _logger.LogInformation("Buluttan sync tamamlandı",
                        new { CorrelationId = correlationId, LocalPath = localPath, Duration = duration.TotalSeconds });
                }
                else
                {
                    _logger.LogError("Buluttan sync başarısız",
                        new { CorrelationId = correlationId, Error = downloadResult.Message });
                }

                return result;
            }
            catch (Exception ex)
            {
                var duration = DateTime.UtcNow - startTime;
                
                _logger.LogError(ex, "Buluttan sync hatası",
                    new { CorrelationId = correlationId, RemotePath = remotePath });

                return new CloudSyncResult
                {
                    Success = false,
                    CorrelationId = correlationId,
                    RemotePath = remotePath,
                    Direction = SyncDirection.FromCloud,
                    Duration = duration,
                    Message = $"Download hatası: {ex.Message}"
                };
            }
        }

        /// <summary>
        /// Bulk upload (birden fazla dosya)
        /// </summary>
        public async Task<List<CloudSyncResult>> BulkSyncToCloudAsync(List<string> localFilePaths, SyncOptions options = null)
        {
            var results = new List<CloudSyncResult>();
            
            _logger.LogInformation("Bulk cloud sync başladı", new { FileCount = localFilePaths.Count });

            // Paralel upload (kontrollü)
            var semaphore = new System.Threading.SemaphoreSlim(3); // Maksimum 3 eşzamanlı upload
            var tasks = localFilePaths.Select(async filePath =>
            {
                await semaphore.WaitAsync();
                try
                {
                    return await SyncToCloudAsync(filePath, options);
                }
                finally
                {
                    semaphore.Release();
                }
            });

            results.AddRange(await Task.WhenAll(tasks));

            var successCount = results.Count(r => r.Success);
            
            _logger.LogInformation("Bulk cloud sync tamamlandı",
                new { TotalFiles = localFilePaths.Count, SuccessCount = successCount, FailureCount = localFilePaths.Count - successCount });

            return results;
        }

        /// <summary>
        /// Aktif provider'ı değiştir
        /// </summary>
        public async Task<bool> SwitchProviderAsync(string newProviderName)
        {
            try
            {
                if (!_providers.ContainsKey(newProviderName))
                {
                    _logger.LogWarning("Bilinmeyen provider", new { ProviderName = newProviderName });
                    return false;
                }

                var newProvider = _providers[newProviderName];
                
                // Yeni provider sağlık kontrolü
                if (!await newProvider.IsHealthyAsync())
                {
                    _logger.LogWarning("Yeni provider sağlıklı değil", new { ProviderName = newProviderName });
                    return false;
                }

                var oldProvider = _activeProviderName;
                _activeProvider = newProvider;
                _activeProviderName = newProviderName;

                _logger.LogInformation("Cloud provider değiştirildi",
                    new { OldProvider = oldProvider, NewProvider = newProviderName });

                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Provider değiştirme hatası", new { NewProvider = newProviderName });
                return false;
            }
        }

        /// <summary>
        /// Mevcut provider'ları listele
        /// </summary>
        public List<string> GetAvailableProviders()
        {
            return _providers.Keys.ToList();
        }
    }
}