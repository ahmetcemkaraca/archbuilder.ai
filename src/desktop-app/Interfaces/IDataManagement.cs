using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ArchBuilder.Desktop.Interfaces
{
    /// <summary>
    /// Lokal veri yönetimi interface'i
    /// </summary>
    public interface ILocalDataManager
    {
        /// <summary>
        /// Revit model verilerini JSON formatında lokal olarak kaydet
        /// </summary>
        Task<LocalDataResult> SaveRevitDataAsync(RevitModelData modelData);

        /// <summary>
        /// Verileri sıkıştırarak kaydet (bulut gönderimi öncesi)
        /// </summary>
        Task<LocalDataResult> SaveCompressedDataAsync(string sourceFilePath, bool deleteSource = false);

        /// <summary>
        /// Sıkıştırılmış veriyi açarak oku
        /// </summary>
        Task<T> ReadCompressedDataAsync<T>(string compressedFilePath) where T : class;

        /// <summary>
        /// Lokal olarak kaydedilmiş veriyi oku
        /// </summary>
        Task<T> ReadLocalDataAsync<T>(string correlationId) where T : class;

        /// <summary>
        /// Veri bütünlüğü doğrulaması
        /// </summary>
        Task<bool> ValidateDataIntegrityAsync(string filePath, string expectedHash);

        /// <summary>
        /// Lokal veri dosyalarını listele
        /// </summary>
        Task<List<LocalDataInfo>> ListLocalDataAsync();

        /// <summary>
        /// Temizlik işlemleri (eski dosyaları sil)
        /// </summary>
        Task<int> CleanupOldDataAsync(TimeSpan olderThan);
    }

    /// <summary>
    /// Cloud Storage provider abstraction interface
    /// </summary>
    public interface ICloudStorageProvider
    {
        /// <summary>
        /// Provider adı (Google Cloud, Oracle Cloud, vs.)
        /// </summary>
        string ProviderName { get; }

        /// <summary>
        /// Dosyayı bulut depolamaya yükle
        /// </summary>
        Task<CloudUploadResult> UploadFileAsync(string localFilePath, string remotePath, UploadOptions options = null);

        /// <summary>
        /// Dosyayı bulut depolamadan indir
        /// </summary>
        Task<CloudDownloadResult> DownloadFileAsync(string remotePath, string localFilePath);

        /// <summary>
        /// Dosyanın bulutta var olup olmadığını kontrol et
        /// </summary>
        Task<bool> FileExistsAsync(string remotePath);

        /// <summary>
        /// Dosyayı bulut depolamadan sil
        /// </summary>
        Task<bool> DeleteFileAsync(string remotePath);

        /// <summary>
        /// Bulut depolama sağlık kontrolü
        /// </summary>
        Task<bool> IsHealthyAsync();

        /// <summary>
        /// Depolama kullanım bilgileri
        /// </summary>
        Task<StorageUsageInfo> GetUsageInfoAsync();
    }

    /// <summary>
    /// Cloud Storage Manager interface
    /// </summary>
    public interface ICloudStorageManager
    {
        /// <summary>
        /// Kullanıcı izni kontrol et
        /// </summary>
        Task<bool> HasUserPermissionAsync();

        /// <summary>
        /// Kullanıcı izni iste
        /// </summary>
        Task<bool> RequestUserPermissionAsync();

        /// <summary>
        /// Lokal dosyayı sıkıştırıp buluta yükle
        /// </summary>
        Task<CloudSyncResult> SyncToCloudAsync(string localFilePath, SyncOptions options = null);

        /// <summary>
        /// Buluttan dosyayı indir ve lokal olarak açarak kaydet
        /// </summary>
        Task<CloudSyncResult> SyncFromCloudAsync(string remotePath, string localPath);

        /// <summary>
        /// Bulk upload (birden fazla dosya)
        /// </summary>
        Task<List<CloudSyncResult>> BulkSyncToCloudAsync(List<string> localFilePaths, SyncOptions options = null);

        /// <summary>
        /// Aktif provider'ı değiştir
        /// </summary>
        Task<bool> SwitchProviderAsync(string newProviderName);

        /// <summary>
        /// Mevcut provider'ları listele
        /// </summary>
        List<string> GetAvailableProviders();
    }
}