using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using Google.Cloud.Storage.V1;
using Google.Apis.Auth.OAuth2;
using ArchBuilder.Desktop.Interfaces;
using ArchBuilder.Desktop.Models;

namespace ArchBuilder.Desktop.Services.CloudProviders
{
    /// <summary>
    /// Google Cloud Storage provider implementasyonu
    /// </summary>
    public class GoogleCloudStorageProvider : ICloudStorageProvider
    {
        private readonly ILogger<GoogleCloudStorageProvider> _logger;
        private readonly IConfiguration _configuration;
        private readonly StorageClient _storageClient;
        private readonly string _bucketName;

        public string ProviderName => "GoogleCloud";

        public GoogleCloudStorageProvider(
            ILogger<GoogleCloudStorageProvider> logger,
            IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            
            // Google Cloud konfigürasyonu
            var projectId = _configuration.GetValue<string>("GoogleCloud:ProjectId");
            var credentialsPath = _configuration.GetValue<string>("GoogleCloud:CredentialsPath");
            _bucketName = _configuration.GetValue<string>("GoogleCloud:BucketName", "archbuilder-revit-data");

            try
            {
                // Service account authentication
                if (!string.IsNullOrEmpty(credentialsPath) && File.Exists(credentialsPath))
                {
                    var credential = GoogleCredential.FromFile(credentialsPath);
                    _storageClient = StorageClient.Create(credential);
                }
                // Application Default Credentials fallback
                else
                {
                    _storageClient = StorageClient.Create();
                }

                _logger.LogInformation("Google Cloud Storage provider başlatıldı",
                    new { ProjectId = projectId, BucketName = _bucketName });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Google Cloud Storage provider başlatma hatası");
                throw;
            }
        }

        /// <summary>
        /// Dosyayı Google Cloud Storage'a yükle
        /// </summary>
        public async Task<CloudUploadResult> UploadFileAsync(string localFilePath, string remotePath, UploadOptions options = null)
        {
            var startTime = DateTime.UtcNow;
            
            try
            {
                options ??= new UploadOptions();
                
                _logger.LogInformation("Google Cloud upload başladı",
                    new { LocalFile = localFilePath, RemotePath = remotePath });

                if (!File.Exists(localFilePath))
                    throw new FileNotFoundException($"Lokal dosya bulunamadı: {localFilePath}");

                var fileInfo = new FileInfo(localFilePath);
                
                // Google Cloud Storage object oluştur
                var storageObject = new Google.Cloud.Storage.V1.Object
                {
                    Bucket = _bucketName,
                    Name = remotePath,
                    ContentType = GetContentType(localFilePath)
                };

                // Metadata ekle
                if (options.Metadata?.Count > 0)
                {
                    storageObject.Metadata = new Dictionary<string, string>(options.Metadata);
                }

                // Upload
                using var fileStream = File.OpenRead(localFilePath);
                var uploadedObject = await _storageClient.UploadObjectAsync(storageObject, fileStream);

                var duration = DateTime.UtcNow - startTime;

                _logger.LogInformation("Google Cloud upload tamamlandı",
                    new { RemotePath = remotePath, SizeBytes = fileInfo.Length, Duration = duration.TotalSeconds });

                return new CloudUploadResult
                {
                    Success = true,
                    RemotePath = remotePath,
                    ETag = uploadedObject.ETag,
                    SizeBytes = fileInfo.Length,
                    UploadDuration = duration,
                    Message = "Upload başarılı",
                    Metadata = new Dictionary<string, object>
                    {
                        ["bucket"] = _bucketName,
                        ["generation"] = uploadedObject.Generation,
                        ["updated"] = uploadedObject.Updated
                    }
                };
            }
            catch (Exception ex)
            {
                var duration = DateTime.UtcNow - startTime;
                
                _logger.LogError(ex, "Google Cloud upload hatası",
                    new { LocalFile = localFilePath, RemotePath = remotePath });

                return new CloudUploadResult
                {
                    Success = false,
                    Message = $"Upload hatası: {ex.Message}",
                    UploadDuration = duration
                };
            }
        }

        /// <summary>
        /// Google Cloud Storage'dan dosya indir
        /// </summary>
        public async Task<CloudDownloadResult> DownloadFileAsync(string remotePath, string localFilePath)
        {
            var startTime = DateTime.UtcNow;
            
            try
            {
                _logger.LogInformation("Google Cloud download başladı",
                    new { RemotePath = remotePath, LocalFile = localFilePath });

                // Dizin oluştur
                var directory = Path.GetDirectoryName(localFilePath);
                if (!string.IsNullOrEmpty(directory))
                    Directory.CreateDirectory(directory);

                // Download
                using var fileStream = File.Create(localFilePath);
                var storageObject = await _storageClient.DownloadObjectAsync(_bucketName, remotePath, fileStream);

                var fileInfo = new FileInfo(localFilePath);
                var duration = DateTime.UtcNow - startTime;

                _logger.LogInformation("Google Cloud download tamamlandı",
                    new { LocalFile = localFilePath, SizeBytes = fileInfo.Length, Duration = duration.TotalSeconds });

                return new CloudDownloadResult
                {
                    Success = true,
                    LocalPath = localFilePath,
                    SizeBytes = fileInfo.Length,
                    DownloadDuration = duration,
                    ETag = storageObject.ETag,
                    Message = "Download başarılı"
                };
            }
            catch (Exception ex)
            {
                var duration = DateTime.UtcNow - startTime;
                
                _logger.LogError(ex, "Google Cloud download hatası",
                    new { RemotePath = remotePath, LocalFile = localFilePath });

                return new CloudDownloadResult
                {
                    Success = false,
                    Message = $"Download hatası: {ex.Message}",
                    DownloadDuration = duration
                };
            }
        }

        /// <summary>
        /// Dosyanın Google Cloud Storage'da var olup olmadığını kontrol et
        /// </summary>
        public async Task<bool> FileExistsAsync(string remotePath)
        {
            try
            {
                var storageObject = await _storageClient.GetObjectAsync(_bucketName, remotePath);
                return storageObject != null;
            }
            catch (GoogleApiException ex) when (ex.HttpStatusCode == System.Net.HttpStatusCode.NotFound)
            {
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Google Cloud file existence check hatası", new { RemotePath = remotePath });
                return false;
            }
        }

        /// <summary>
        /// Google Cloud Storage'dan dosya sil
        /// </summary>
        public async Task<bool> DeleteFileAsync(string remotePath)
        {
            try
            {
                await _storageClient.DeleteObjectAsync(_bucketName, remotePath);
                
                _logger.LogInformation("Google Cloud dosya silindi", new { RemotePath = remotePath });
                
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Google Cloud delete hatası", new { RemotePath = remotePath });
                return false;
            }
        }

        /// <summary>
        /// Google Cloud Storage sağlık kontrolü
        /// </summary>
        public async Task<bool> IsHealthyAsync()
        {
            try
            {
                // Basit bir bucket bilgisi al
                var bucket = await _storageClient.GetBucketAsync(_bucketName);
                return bucket != null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Google Cloud sağlık kontrolü hatası");
                return false;
            }
        }

        /// <summary>
        /// Google Cloud Storage kullanım bilgileri
        /// </summary>
        public async Task<StorageUsageInfo> GetUsageInfoAsync()
        {
            try
            {
                var objects = _storageClient.ListObjectsAsync(_bucketName);
                
                long totalSize = 0;
                int fileCount = 0;

                await foreach (var obj in objects)
                {
                    totalSize += obj.Size ?? 0;
                    fileCount++;
                }

                return new StorageUsageInfo
                {
                    UsedSpaceBytes = totalSize,
                    FileCount = fileCount,
                    LastUpdated = DateTime.UtcNow,
                    // Google Cloud'da toplam alan sınırı genelde yok
                    TotalSpaceBytes = long.MaxValue,
                    AvailableSpaceBytes = long.MaxValue - totalSize
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Google Cloud usage info hatası");
                
                return new StorageUsageInfo
                {
                    LastUpdated = DateTime.UtcNow
                };
            }
        }

        #region Private Methods

        private static string GetContentType(string filePath)
        {
            var extension = Path.GetExtension(filePath).ToLowerInvariant();
            
            return extension switch
            {
                ".json" => "application/json",
                ".gz" => "application/gzip",
                ".zip" => "application/zip",
                ".txt" => "text/plain",
                ".log" => "text/plain",
                _ => "application/octet-stream"
            };
        }

        #endregion
    }
}