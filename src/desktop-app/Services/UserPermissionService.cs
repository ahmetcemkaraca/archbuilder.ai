using System;
using System.Threading.Tasks;
using System.Windows;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Configuration;
using ArchBuilder.Desktop.Views.Dialogs;

namespace ArchBuilder.Desktop.Services
{
    /// <summary>
    /// Kullanıcı izin yönetimi servisi
    /// </summary>
    public interface IUserPermissionService
    {
        /// <summary>
        /// Bulut sync izni var mı kontrol et
        /// </summary>
        Task<bool> HasCloudSyncPermissionAsync();

        /// <summary>
        /// Kullanıcıdan bulut sync izni iste
        /// </summary>
        Task<bool> RequestCloudSyncPermissionAsync();

        /// <summary>
        /// İzin durumunu sıfırla (test için)
        /// </summary>
        Task ResetPermissionsAsync();
    }

    /// <summary>
    /// Kullanıcı izin yönetimi implementasyonu
    /// </summary>
    public class UserPermissionService : IUserPermissionService
    {
        private readonly ILogger<UserPermissionService> _logger;
        private readonly IConfiguration _configuration;
        
        // İzin durumları (gerçek uygulamada registry/config'de saklanır)
        private static bool? _cloudSyncPermissionGranted = null;
        private static DateTime? _permissionGrantedAt = null;

        public UserPermissionService(
            ILogger<UserPermissionService> logger,
            IConfiguration configuration)
        {
            _logger = logger;
            _configuration = configuration;
        }

        /// <summary>
        /// Bulut sync izni var mı kontrol et
        /// </summary>
        public Task<bool> HasCloudSyncPermissionAsync()
        {
            try
            {
                // İzin daha önce verilmiş mi?
                if (_cloudSyncPermissionGranted.HasValue && _cloudSyncPermissionGranted.Value)
                {
                    // İzin süresi kontrol et (örnek: 30 gün)
                    var permissionExpiry = _configuration.GetValue<int>("UserPermissions:CloudSyncExpiryDays", 30);
                    
                    if (_permissionGrantedAt.HasValue && 
                        DateTime.UtcNow - _permissionGrantedAt.Value <= TimeSpan.FromDays(permissionExpiry))
                    {
                        _logger.LogInformation("Bulut sync izni mevcut ve geçerli",
                            new { GrantedAt = _permissionGrantedAt.Value, ExpiryDays = permissionExpiry });
                        
                        return Task.FromResult(true);
                    }
                    else
                    {
                        _logger.LogInformation("Bulut sync izni süresi dolmuş", 
                            new { GrantedAt = _permissionGrantedAt.Value });
                        
                        // İzin süresini sıfırla
                        _cloudSyncPermissionGranted = null;
                        _permissionGrantedAt = null;
                    }
                }

                return Task.FromResult(false);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "İzin kontrolü hatası");
                return Task.FromResult(false);
            }
        }

        /// <summary>
        /// Kullanıcıdan bulut sync izni iste
        /// </summary>
        public async Task<bool> RequestCloudSyncPermissionAsync()
        {
            try
            {
                _logger.LogInformation("Kullanıcıdan bulut sync izni isteniyor");

                // UI thread'de dialog göster
                var permissionGranted = false;
                
                await Application.Current.Dispatcher.InvokeAsync(() =>
                {
                    var dialog = new CloudSyncPermissionDialog
                    {
                        Owner = Application.Current.MainWindow
                    };

                    var result = dialog.ShowDialog();
                    permissionGranted = result == true;
                });

                if (permissionGranted)
                {
                    _cloudSyncPermissionGranted = true;
                    _permissionGrantedAt = DateTime.UtcNow;
                    
                    _logger.LogInformation("Kullanıcı bulut sync iznini verdi",
                        new { GrantedAt = _permissionGrantedAt.Value });
                }
                else
                {
                    _cloudSyncPermissionGranted = false;
                    _permissionGrantedAt = null;
                    
                    _logger.LogInformation("Kullanıcı bulut sync iznini reddetti");
                }

                return permissionGranted;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "İzin isteme hatası");
                return false;
            }
        }

        /// <summary>
        /// İzin durumunu sıfırla (test için)
        /// </summary>
        public Task ResetPermissionsAsync()
        {
            _cloudSyncPermissionGranted = null;
            _permissionGrantedAt = null;
            
            _logger.LogInformation("Kullanıcı izinleri sıfırlandı");
            
            return Task.CompletedTask;
        }
    }
}