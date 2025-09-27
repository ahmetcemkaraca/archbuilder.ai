using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using Oci.ObjectstorageService;
using Oci.ObjectstorageService.Models;
using Oci.ObjectstorageService.Requests;
using Oci.Common.Auth;
using ArchBuilder.Desktop.Interfaces;
using ArchBuilder.Desktop.Models;

namespace ArchBuilder.Desktop.Services.CloudProviders
{
    /// <summary>
    /// Oracle Cloud Infrastructure Object Storage provider implementasyonu
    /// </summary>
    public class OracleCloudStorageProvider : ICloudStorageProvider
    {
        private readonly ILogger<OracleCloudStorageProvider> _logger;
        private readonly IConfiguration _configuration;
        private readonly ObjectStorageClient _objectStorageClient;
        private readonly string _namespaceName;
        private readonly string _bucketName;
        private readonly string _compartmentId;

        public string ProviderName => "OracleCloud";

        public OracleCloudStorageProvider(
            ILogger<OracleCloudStorageProvider> logger,
            IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
            
            // Oracle Cloud konfigürasyonu
            var configFilePath = _configuration.GetValue<string>("OracleCloud:ConfigFilePath");
            var profile = _configuration.GetValue<string>("OracleCloud:Profile", "DEFAULT");
            _namespaceName = _configuration.GetValue<string>("OracleCloud:NamespaceName");
            _bucketName = _configuration.GetValue<string>("OracleCloud:BucketName", "archbuilder-revit-data");
            _compartmentId = _configuration.GetValue<string>("OracleCloud:CompartmentId");

            try
            {
                // Authentication provider
                IAuthenticationDetailsProvider authProvider;
                
                if (!string.IsNullOrEmpty(configFilePath) && File.Exists(configFilePath))
                {
                    authProvider = new ConfigFileAuthenticationDetailsProvider(configFilePath, profile);
                }
                else
                {
                    // Instance Principal fallback (OCI compute instance üzerinde çalışırken)
                    authProvider = InstancePrincipalsAuthenticationDetailsProvider.Builder().Build();
                }

                _objectStorageClient = new ObjectStorageClient(authProvider);

                _logger.LogInformation("Oracle Cloud Storage provider başlatıldı",
                    new { NamespaceName = _namespaceName, BucketName = _bucketName, CompartmentId = _compartmentId });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Oracle Cloud Storage provider başlatma hatası");
                throw;
            }
        }

        /// <summary>
        /// Dosyayı Oracle Cloud Object Storage'a yükle
        /// </summary>
        public async Task<CloudUploadResult> UploadFileAsync(string localFilePath, string remotePath, UploadOptions options = null)
        {
            var startTime = DateTime.UtcNow;
            
            try
            {
                options ??= new UploadOptions();
                
                _logger.LogInformation("Oracle Cloud upload başladı",
                    new { LocalFile = localFilePath, RemotePath = remotePath });

                if (!File.Exists(localFilePath))
                    throw new FileNotFoundException($"Lokal dosya bulunamadı: {localFilePath}");

                var fileInfo = new FileInfo(localFilePath);
                
                // Put object request oluştur
                var putObjectRequest = new PutObjectRequest
                {
                    NamespaceName = _namespaceName,
                    BucketName = _bucketName,
                    ObjectName = remotePath,
                    ContentType = GetContentType(localFilePath),
                    ContentLength = fileInfo.Length,
                    PutObjectBody = File.OpenRead(localFilePath)
                };

                // Metadata ekle
                if (options.Metadata?.Count > 0)
                {
                    putObjectRequest.OpcMeta = new Dictionary<string, string>(options.Metadata);
                }

                // Upload
                var response = await _objectStorageClient.PutObject(putObjectRequest);

                var duration = DateTime.UtcNow - startTime;

                _logger.LogInformation("Oracle Cloud upload tamamlandı",
                    new { RemotePath = remotePath, SizeBytes = fileInfo.Length, Duration = duration.TotalSeconds });

                return new CloudUploadResult
                {
                    Success = true,
                    RemotePath = remotePath,
                    ETag = response.ETag,
                    SizeBytes = fileInfo.Length,
                    UploadDuration = duration,
                    Message = "Upload başarılı",
                    Metadata = new Dictionary<string, object>
                    {
                        ["namespace"] = _namespaceName,
                        ["bucket"] = _bucketName,
                        ["requestId"] = response.OpcRequestId,
                        ["lastModified"] = response.LastModified
                    }
                };
            }
            catch (Exception ex)
            {
                var duration = DateTime.UtcNow - startTime;
                
                _logger.LogError(ex, "Oracle Cloud upload hatası",
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
        /// Oracle Cloud Object Storage'dan dosya indir
        /// </summary>
        public async Task<CloudDownloadResult> DownloadFileAsync(string remotePath, string localFilePath)
        {
            var startTime = DateTime.UtcNow;
            
            try
            {
                _logger.LogInformation("Oracle Cloud download başladı",
                    new { RemotePath = remotePath, LocalFile = localFilePath });

                // Dizin oluştur
                var directory = Path.GetDirectoryName(localFilePath);
                if (!string.IsNullOrEmpty(directory))
                    Directory.CreateDirectory(directory);

                // Get object request
                var getObjectRequest = new GetObjectRequest
                {
                    NamespaceName = _namespaceName,
                    BucketName = _bucketName,
                    ObjectName = remotePath
                };

                // Download
                var response = await _objectStorageClient.GetObject(getObjectRequest);
                
                using var fileStream = File.Create(localFilePath);
                await response.InputStream.CopyToAsync(fileStream);

                var fileInfo = new FileInfo(localFilePath);
                var duration = DateTime.UtcNow - startTime;

                _logger.LogInformation("Oracle Cloud download tamamlandı",
                    new { LocalFile = localFilePath, SizeBytes = fileInfo.Length, Duration = duration.TotalSeconds });

                return new CloudDownloadResult
                {
                    Success = true,
                    LocalPath = localFilePath,
                    SizeBytes = fileInfo.Length,
                    DownloadDuration = duration,
                    ETag = response.ETag,
                    Message = "Download başarılı"
                };
            }
            catch (Exception ex)
            {
                var duration = DateTime.UtcNow - startTime;
                
                _logger.LogError(ex, "Oracle Cloud download hatası",
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
        /// Dosyanın Oracle Cloud Object Storage'da var olup olmadığını kontrol et
        /// </summary>
        public async Task<bool> FileExistsAsync(string remotePath)
        {
            try
            {
                var headObjectRequest = new HeadObjectRequest
                {
                    NamespaceName = _namespaceName,
                    BucketName = _bucketName,
                    ObjectName = remotePath
                };

                var response = await _objectStorageClient.HeadObject(headObjectRequest);
                return response != null;
            }
            catch (Oci.Common.OciException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
            {
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Oracle Cloud file existence check hatası", new { RemotePath = remotePath });
                return false;
            }
        }

        /// <summary>
        /// Oracle Cloud Object Storage'dan dosya sil
        /// </summary>
        public async Task<bool> DeleteFileAsync(string remotePath)
        {
            try
            {
                var deleteObjectRequest = new DeleteObjectRequest
                {
                    NamespaceName = _namespaceName,
                    BucketName = _bucketName,
                    ObjectName = remotePath
                };

                await _objectStorageClient.DeleteObject(deleteObjectRequest);
                
                _logger.LogInformation("Oracle Cloud dosya silindi", new { RemotePath = remotePath });
                
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Oracle Cloud delete hatası", new { RemotePath = remotePath });
                return false;
            }
        }

        /// <summary>
        /// Oracle Cloud Object Storage sağlık kontrolü
        /// </summary>
        public async Task<bool> IsHealthyAsync()
        {
            try
            {
                // Basit bir bucket bilgisi al
                var getBucketRequest = new GetBucketRequest
                {
                    NamespaceName = _namespaceName,
                    BucketName = _bucketName
                };

                var response = await _objectStorageClient.GetBucket(getBucketRequest);
                return response?.Bucket != null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Oracle Cloud sağlık kontrolü hatası");
                return false;
            }
        }

        /// <summary>
        /// Oracle Cloud Object Storage kullanım bilgileri
        /// </summary>
        public async Task<StorageUsageInfo> GetUsageInfoAsync()
        {
            try
            {
                var listObjectsRequest = new ListObjectsRequest
                {
                    NamespaceName = _namespaceName,
                    BucketName = _bucketName
                };

                var response = await _objectStorageClient.ListObjects(listObjectsRequest);
                
                long totalSize = 0;
                int fileCount = 0;

                if (response.ListObjects?.Objects != null)
                {
                    foreach (var obj in response.ListObjects.Objects)
                    {
                        totalSize += obj.Size ?? 0;
                        fileCount++;
                    }
                }

                return new StorageUsageInfo
                {
                    UsedSpaceBytes = totalSize,
                    FileCount = fileCount,
                    LastUpdated = DateTime.UtcNow,
                    // Oracle Cloud'da toplam alan sınırı genelde yok
                    TotalSpaceBytes = long.MaxValue,
                    AvailableSpaceBytes = long.MaxValue - totalSize
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Oracle Cloud usage info hatası");
                
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

        protected virtual void Dispose(bool disposing)
        {
            if (disposing)
            {
                _objectStorageClient?.Dispose();
            }
        }

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }
    }
}