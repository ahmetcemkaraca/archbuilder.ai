using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Linq;
using ArchBuilder.Desktop.Services;

namespace ArchBuilder.Desktop.ViewModels
{
    /// <summary>
    /// TR: Gelişmiş ayarlar view model - P33-T1, P33-T2, P33-T3
    /// </summary>
    public class SettingsViewModel : INotifyPropertyChanged
    {
        private readonly SettingsService _settingsService;
        private readonly LoggingService _loggingService;
        
        // TR: Tab control
        private int _selectedTabIndex = 0;
        
        // TR: API Settings
        private string _apiBaseUrl = "https://api.archbuilder.app/v1";
        private string _apiKey = "";
        private int _requestTimeout = 30;
        private bool _enableLogging = true;
        
        // TR: Regional Settings
        private LanguageItem _selectedLanguage;
        private RegionItem _selectedRegion;
        private BuildingTypeItem _selectedBuildingType;
        
        // TR: Validation Settings
        private bool _enableGeometricValidation = true;
        private bool _enableCodeValidation = true;
        private bool _autoSubmitForReview = false;
        
        // TR: UI Settings
        private ThemeItem _selectedTheme;
        private bool _useSystemTheme = true;
        private bool _enableAnimations = true;
        private bool _rememberWindowPosition = true;
        private bool _minimizeToTray = false;
        private bool _showNotifications = true;
        
        // TR: Performance Settings
        private double _cacheSize = 100;
        private int _maxConcurrentRequests = 5;
        private bool _enablePerformanceMonitoring = false;
        
        // TR: Debug Settings
        private LogLevelItem _selectedLogLevel;
        private bool _enableDebugMode = false;
        private bool _enableTelemetry = true;
        
        public SettingsViewModel(SettingsService settingsService, LoggingService loggingService)
        {
            _settingsService = settingsService ?? throw new ArgumentNullException(nameof(settingsService));
            _loggingService = loggingService ?? throw new ArgumentNullException(nameof(loggingService));
            
            // TR: Initialize commands
            SaveCommand = new RelayCommand(async () => await SaveSettingsAsync());
            ResetCommand = new RelayCommand(() => ResetToDefaults());
            CloseCommand = new RelayCommand(() => CloseWindow());
            
            // TR: Initialize collections
            InitializeCollections();
            
            // TR: Load settings
            LoadSettings();
        }
        
        #region Properties
        
        // TR: Window title
        public string WindowTitle => GetLocalizedString("SettingsWindowTitle");
        
        // TR: Tab control
        public int SelectedTabIndex
        {
            get => _selectedTabIndex;
            set => SetProperty(ref _selectedTabIndex, value);
        }
        
        // TR: API Settings
        public string ApiBaseUrl
        {
            get => _apiBaseUrl;
            set => SetProperty(ref _apiBaseUrl, value);
        }
        
        public string ApiKey
        {
            get => _apiKey;
            set => SetProperty(ref _apiKey, value);
        }
        
        public int RequestTimeout
        {
            get => _requestTimeout;
            set => SetProperty(ref _requestTimeout, value);
        }
        
        public bool EnableLogging
        {
            get => _enableLogging;
            set => SetProperty(ref _enableLogging, value);
        }
        
        // TR: Regional Settings
        public LanguageItem SelectedLanguage
        {
            get => _selectedLanguage;
            set
            {
                if (SetProperty(ref _selectedLanguage, value))
                {
                    OnLanguageChanged();
                }
            }
        }
        
        public RegionItem SelectedRegion
        {
            get => _selectedRegion;
            set
            {
                if (SetProperty(ref _selectedRegion, value))
                {
                    OnRegionChanged();
                }
            }
        }
        
        public BuildingTypeItem SelectedBuildingType
        {
            get => _selectedBuildingType;
            set => SetProperty(ref _selectedBuildingType, value);
        }
        
        // TR: Validation Settings
        public bool EnableGeometricValidation
        {
            get => _enableGeometricValidation;
            set => SetProperty(ref _enableGeometricValidation, value);
        }
        
        public bool EnableCodeValidation
        {
            get => _enableCodeValidation;
            set => SetProperty(ref _enableCodeValidation, value);
        }
        
        public bool AutoSubmitForReview
        {
            get => _autoSubmitForReview;
            set => SetProperty(ref _autoSubmitForReview, value);
        }
        
        // TR: UI Settings
        public ThemeItem SelectedTheme
        {
            get => _selectedTheme;
            set => SetProperty(ref _selectedTheme, value);
        }
        
        public bool UseSystemTheme
        {
            get => _useSystemTheme;
            set => SetProperty(ref _useSystemTheme, value);
        }
        
        public bool EnableAnimations
        {
            get => _enableAnimations;
            set => SetProperty(ref _enableAnimations, value);
        }
        
        public bool RememberWindowPosition
        {
            get => _rememberWindowPosition;
            set => SetProperty(ref _rememberWindowPosition, value);
        }
        
        public bool MinimizeToTray
        {
            get => _minimizeToTray;
            set => SetProperty(ref _minimizeToTray, value);
        }
        
        public bool ShowNotifications
        {
            get => _showNotifications;
            set => SetProperty(ref _showNotifications, value);
        }
        
        // TR: Performance Settings
        public double CacheSize
        {
            get => _cacheSize;
            set => SetProperty(ref _cacheSize, value);
        }
        
        public int MaxConcurrentRequests
        {
            get => _maxConcurrentRequests;
            set => SetProperty(ref _maxConcurrentRequests, value);
        }
        
        public bool EnablePerformanceMonitoring
        {
            get => _enablePerformanceMonitoring;
            set => SetProperty(ref _enablePerformanceMonitoring, value);
        }
        
        // TR: Debug Settings
        public LogLevelItem SelectedLogLevel
        {
            get => _selectedLogLevel;
            set => SetProperty(ref _selectedLogLevel, value);
        }
        
        public bool EnableDebugMode
        {
            get => _enableDebugMode;
            set => SetProperty(ref _enableDebugMode, value);
        }
        
        public bool EnableTelemetry
        {
            get => _enableTelemetry;
            set => SetProperty(ref _enableTelemetry, value);
        }
        
        // TR: Collections
        public ObservableCollection<LanguageItem> AvailableLanguages { get; } = new ObservableCollection<LanguageItem>();
        public ObservableCollection<RegionItem> AvailableRegions { get; } = new ObservableCollection<RegionItem>();
        public ObservableCollection<BuildingTypeItem> AvailableBuildingTypes { get; } = new ObservableCollection<BuildingTypeItem>();
        public ObservableCollection<ThemeItem> AvailableThemes { get; } = new ObservableCollection<ThemeItem>();
        public ObservableCollection<LogLevelItem> AvailableLogLevels { get; } = new ObservableCollection<LogLevelItem>();
        
        #endregion
        
        #region Localized Strings
        
        public string GeneralTabLabel => GetLocalizedString("GeneralTabLabel");
        public string UiTabLabel => GetLocalizedString("UiTabLabel");
        public string AdvancedTabLabel => GetLocalizedString("AdvancedTabLabel");
        public string ApiSettingsLabel => GetLocalizedString("ApiSettingsLabel");
        public string ApiBaseUrlLabel => GetLocalizedString("ApiBaseUrlLabel");
        public string ApiKeyLabel => GetLocalizedString("ApiKeyLabel");
        public string TimeoutLabel => GetLocalizedString("TimeoutLabel");
        public string EnableLoggingLabel => GetLocalizedString("EnableLoggingLabel");
        public string RegionalSettingsLabel => GetLocalizedString("RegionalSettingsLabel");
        public string LanguageLabel => GetLocalizedString("LanguageLabel");
        public string RegionLabel => GetLocalizedString("RegionLabel");
        public string BuildingTypeLabel => GetLocalizedString("BuildingTypeLabel");
        public string ValidationSettingsLabel => GetLocalizedString("ValidationSettingsLabel");
        public string EnableGeometricValidationLabel => GetLocalizedString("EnableGeometricValidationLabel");
        public string EnableCodeValidationLabel => GetLocalizedString("EnableCodeValidationLabel");
        public string AutoSubmitForReviewLabel => GetLocalizedString("AutoSubmitForReviewLabel");
        public string ThemeSettingsLabel => GetLocalizedString("ThemeSettingsLabel");
        public string ThemeLabel => GetLocalizedString("ThemeLabel");
        public string UseSystemThemeLabel => GetLocalizedString("UseSystemThemeLabel");
        public string EnableAnimationsLabel => GetLocalizedString("EnableAnimationsLabel");
        public string WindowSettingsLabel => GetLocalizedString("WindowSettingsLabel");
        public string RememberWindowPositionLabel => GetLocalizedString("RememberWindowPositionLabel");
        public string MinimizeToTrayLabel => GetLocalizedString("MinimizeToTrayLabel");
        public string ShowNotificationsLabel => GetLocalizedString("ShowNotificationsLabel");
        public string PerformanceSettingsLabel => GetLocalizedString("PerformanceSettingsLabel");
        public string CacheSizeLabel => GetLocalizedString("CacheSizeLabel");
        public string MaxConcurrentRequestsLabel => GetLocalizedString("MaxConcurrentRequestsLabel");
        public string EnablePerformanceMonitoringLabel => GetLocalizedString("EnablePerformanceMonitoringLabel");
        public string DebugSettingsLabel => GetLocalizedString("DebugSettingsLabel");
        public string LogLevelLabel => GetLocalizedString("LogLevelLabel");
        public string EnableDebugModeLabel => GetLocalizedString("EnableDebugModeLabel");
        public string EnableTelemetryLabel => GetLocalizedString("EnableTelemetryLabel");
        public string ResetButtonLabel => GetLocalizedString("ResetButtonLabel");
        public string SaveButtonLabel => GetLocalizedString("SaveButtonLabel");
        public string CloseButtonLabel => GetLocalizedString("CloseButtonLabel");
        
        #endregion
        
        #region Commands
        
        public ICommand SaveCommand { get; }
        public ICommand ResetCommand { get; }
        public ICommand CloseCommand { get; }
        
        #endregion
        
        #region Methods
        
        private void InitializeCollections()
        {
            // TR: Available languages
            AvailableLanguages.Add(new LanguageItem { Code = "tr", Name = "Türkçe" });
            AvailableLanguages.Add(new LanguageItem { Code = "en", Name = "English" });
            
            // TR: Available regions
            AvailableRegions.Add(new RegionItem { Code = "TR", Name = "Türkiye" });
            AvailableRegions.Add(new RegionItem { Code = "US", Name = "United States" });
            AvailableRegions.Add(new RegionItem { Code = "EU", Name = "European Union" });
            
            // TR: Available themes
            AvailableThemes.Add(new ThemeItem { Code = "light", Name = "TR: Açık Tema" });
            AvailableThemes.Add(new ThemeItem { Code = "dark", Name = "TR: Koyu Tema" });
            AvailableThemes.Add(new ThemeItem { Code = "auto", Name = "TR: Otomatik" });
            
            // TR: Available log levels
            AvailableLogLevels.Add(new LogLevelItem { Code = "trace", Name = "TR: Trace" });
            AvailableLogLevels.Add(new LogLevelItem { Code = "debug", Name = "TR: Debug" });
            AvailableLogLevels.Add(new LogLevelItem { Code = "info", Name = "TR: Info" });
            AvailableLogLevels.Add(new LogLevelItem { Code = "warn", Name = "TR: Warning" });
            AvailableLogLevels.Add(new LogLevelItem { Code = "error", Name = "TR: Error" });
        }
        
        private void OnLanguageChanged()
        {
            // TR: Language değiştiğinde building types'ı güncelle
            UpdateBuildingTypesForRegion();
        }
        
        private void OnRegionChanged()
        {
            // TR: Region değiştiğinde building types'ı güncelle
            UpdateBuildingTypesForRegion();
        }
        
        private void UpdateBuildingTypesForRegion()
        {
            AvailableBuildingTypes.Clear();
            
            if (_selectedRegion?.Code == "TR")
            {
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "residential", Name = "TR: Konut" });
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "commercial", Name = "TR: Ticari" });
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "industrial", Name = "TR: Endüstriyel" });
            }
            else if (_selectedRegion?.Code == "US")
            {
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "residential", Name = "TR: Residential" });
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "commercial", Name = "TR: Commercial" });
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "industrial", Name = "TR: Industrial" });
            }
            else
            {
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "residential", Name = "TR: Residential" });
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "commercial", Name = "TR: Commercial" });
                AvailableBuildingTypes.Add(new BuildingTypeItem { Code = "industrial", Name = "TR: Industrial" });
            }
        }
        
        private void LoadSettings()
        {
            try
            {
                // TR: Settings service'den ayarları yükle
                var settings = _settingsService.LoadSettings();
                
                ApiBaseUrl = settings.ApiBaseUrl;
                ApiKey = settings.ApiKey;
                RequestTimeout = settings.RequestTimeout;
                EnableLogging = settings.EnableLogging;
                
                // TR: Regional settings
                SelectedLanguage = AvailableLanguages.FirstOrDefault(l => l.Code == settings.Language) ?? AvailableLanguages.First();
                SelectedRegion = AvailableRegions.FirstOrDefault(r => r.Code == settings.Region) ?? AvailableRegions.First();
                UpdateBuildingTypesForRegion();
                SelectedBuildingType = AvailableBuildingTypes.FirstOrDefault(bt => bt.Code == settings.BuildingType) ?? AvailableBuildingTypes.First();
                
                // TR: Validation settings
                EnableGeometricValidation = settings.EnableGeometricValidation;
                EnableCodeValidation = settings.EnableCodeValidation;
                AutoSubmitForReview = settings.AutoSubmitForReview;
                
                // TR: UI settings
                SelectedTheme = AvailableThemes.FirstOrDefault(t => t.Code == settings.Theme) ?? AvailableThemes.First();
                UseSystemTheme = settings.UseSystemTheme;
                EnableAnimations = settings.EnableAnimations;
                RememberWindowPosition = settings.RememberWindowPosition;
                MinimizeToTray = settings.MinimizeToTray;
                ShowNotifications = settings.ShowNotifications;
                
                // TR: Performance settings
                CacheSize = settings.CacheSize;
                MaxConcurrentRequests = settings.MaxConcurrentRequests;
                EnablePerformanceMonitoring = settings.EnablePerformanceMonitoring;
                
                // TR: Debug settings
                SelectedLogLevel = AvailableLogLevels.FirstOrDefault(ll => ll.Code == settings.LogLevel) ?? AvailableLogLevels.First();
                EnableDebugMode = settings.EnableDebugMode;
                EnableTelemetry = settings.EnableTelemetry;
                
                _loggingService.LogInfo("TR: Ayarlar yüklendi");
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Ayarlar yükleme hatası: {ex.Message}");
            }
        }
        
        private async Task SaveSettingsAsync()
        {
            try
            {
                var settings = new AppSettings
                {
                    ApiBaseUrl = ApiBaseUrl,
                    ApiKey = ApiKey,
                    RequestTimeout = RequestTimeout,
                    EnableLogging = EnableLogging,
                    Language = SelectedLanguage?.Code ?? "tr",
                    Region = SelectedRegion?.Code ?? "TR",
                    BuildingType = SelectedBuildingType?.Code ?? "residential",
                    EnableGeometricValidation = EnableGeometricValidation,
                    EnableCodeValidation = EnableCodeValidation,
                    AutoSubmitForReview = AutoSubmitForReview,
                    Theme = SelectedTheme?.Code ?? "auto",
                    UseSystemTheme = UseSystemTheme,
                    EnableAnimations = EnableAnimations,
                    RememberWindowPosition = RememberWindowPosition,
                    MinimizeToTray = MinimizeToTray,
                    ShowNotifications = ShowNotifications,
                    CacheSize = CacheSize,
                    MaxConcurrentRequests = MaxConcurrentRequests,
                    EnablePerformanceMonitoring = EnablePerformanceMonitoring,
                    LogLevel = SelectedLogLevel?.Code ?? "info",
                    EnableDebugMode = EnableDebugMode,
                    EnableTelemetry = EnableTelemetry
                };
                
                await _settingsService.SaveSettingsAsync(settings);
                _loggingService.LogInfo("TR: Ayarlar kaydedildi");
                
                CloseWindow();
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Ayarlar kaydetme hatası: {ex.Message}");
            }
        }
        
        private void ResetToDefaults()
        {
            try
            {
                // TR: Default değerlere sıfırla
                ApiBaseUrl = "https://api.archbuilder.app/v1";
                ApiKey = "";
                RequestTimeout = 30;
                EnableLogging = true;
                
                SelectedLanguage = AvailableLanguages.FirstOrDefault(l => l.Code == "tr");
                SelectedRegion = AvailableRegions.FirstOrDefault(r => r.Code == "TR");
                UpdateBuildingTypesForRegion();
                SelectedBuildingType = AvailableBuildingTypes.FirstOrDefault(bt => bt.Code == "residential");
                
                EnableGeometricValidation = true;
                EnableCodeValidation = true;
                AutoSubmitForReview = false;
                
                SelectedTheme = AvailableThemes.FirstOrDefault(t => t.Code == "auto");
                UseSystemTheme = true;
                EnableAnimations = true;
                RememberWindowPosition = true;
                MinimizeToTray = false;
                ShowNotifications = true;
                
                CacheSize = 100;
                MaxConcurrentRequests = 5;
                EnablePerformanceMonitoring = false;
                
                SelectedLogLevel = AvailableLogLevels.FirstOrDefault(ll => ll.Code == "info");
                EnableDebugMode = false;
                EnableTelemetry = true;
                
                _loggingService.LogInfo("TR: Ayarlar varsayılan değerlere sıfırlandı");
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Ayarlar sıfırlama hatası: {ex.Message}");
            }
        }
        
        private void CloseWindow()
        {
            // TR: Parent window'u kapat
            if (System.Windows.Application.Current.MainWindow != null)
            {
                System.Windows.Application.Current.MainWindow.Close();
            }
        }
        
        private string GetLocalizedString(string key)
        {
            // TR: Localization service'den string getir
            // Şimdilik hardcoded değerler döndürüyoruz
            return key switch
            {
                "SettingsWindowTitle" => "TR: Ayarlar",
                "GeneralTabLabel" => "TR: Genel",
                "UiTabLabel" => "TR: Kullanıcı Arayüzü",
                "AdvancedTabLabel" => "TR: Gelişmiş",
                "ApiSettingsLabel" => "TR: API Ayarları",
                "ApiBaseUrlLabel" => "TR: API Base URL:",
                "ApiKeyLabel" => "TR: API Key:",
                "TimeoutLabel" => "TR: Timeout (saniye):",
                "EnableLoggingLabel" => "TR: Logging'i etkinleştir",
                "RegionalSettingsLabel" => "TR: Bölgesel Ayarlar",
                "LanguageLabel" => "TR: Dil:",
                "RegionLabel" => "TR: Bölge:",
                "BuildingTypeLabel" => "TR: Bina Tipi:",
                "ValidationSettingsLabel" => "TR: Validation Ayarları",
                "EnableGeometricValidationLabel" => "TR: Geometrik validation'ı etkinleştir",
                "EnableCodeValidationLabel" => "TR: Kod validation'ını etkinleştir",
                "AutoSubmitForReviewLabel" => "TR: Otomatik review gönder",
                "ThemeSettingsLabel" => "TR: Tema Ayarları",
                "ThemeLabel" => "TR: Tema:",
                "UseSystemThemeLabel" => "TR: Sistem temasını kullan",
                "EnableAnimationsLabel" => "TR: Animasyonları etkinleştir",
                "WindowSettingsLabel" => "TR: Pencere Ayarları",
                "RememberWindowPositionLabel" => "TR: Pencere pozisyonunu hatırla",
                "MinimizeToTrayLabel" => "TR: Sisteme küçült",
                "ShowNotificationsLabel" => "TR: Bildirimleri göster",
                "PerformanceSettingsLabel" => "TR: Performans Ayarları",
                "CacheSizeLabel" => "TR: Cache Boyutu (MB):",
                "MaxConcurrentRequestsLabel" => "TR: Maks. Eşzamanlı İstek:",
                "EnablePerformanceMonitoringLabel" => "TR: Performans izlemeyi etkinleştir",
                "DebugSettingsLabel" => "TR: Debug Ayarları",
                "LogLevelLabel" => "TR: Log Seviyesi:",
                "EnableDebugModeLabel" => "TR: Debug modunu etkinleştir",
                "EnableTelemetryLabel" => "TR: Telemetriyi etkinleştir",
                "ResetButtonLabel" => "TR: Sıfırla",
                "SaveButtonLabel" => "TR: Kaydet",
                "CloseButtonLabel" => "TR: Kapat",
                _ => key
            };
        }
        
        #endregion
        
        #region INotifyPropertyChanged
        
        public event PropertyChangedEventHandler PropertyChanged;
        
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
        
        protected bool SetProperty<T>(ref T field, T value, [CallerMemberName] string propertyName = null)
        {
            if (Equals(field, value)) return false;
            field = value;
            OnPropertyChanged(propertyName);
            return true;
        }
        
        #endregion
    }
    
    #region Model Classes
    
    public class LanguageItem
    {
        public string Code { get; set; }
        public string Name { get; set; }
    }
    
    public class RegionItem
    {
        public string Code { get; set; }
        public string Name { get; set; }
    }
    
    public class BuildingTypeItem
    {
        public string Code { get; set; }
        public string Name { get; set; }
    }
    
    public class ThemeItem
    {
        public string Code { get; set; }
        public string Name { get; set; }
    }
    
    public class LogLevelItem
    {
        public string Code { get; set; }
        public string Name { get; set; }
    }
    
    public class AppSettings
    {
        public string ApiBaseUrl { get; set; }
        public string ApiKey { get; set; }
        public int RequestTimeout { get; set; }
        public bool EnableLogging { get; set; }
        public string Language { get; set; }
        public string Region { get; set; }
        public string BuildingType { get; set; }
        public bool EnableGeometricValidation { get; set; }
        public bool EnableCodeValidation { get; set; }
        public bool AutoSubmitForReview { get; set; }
        public string Theme { get; set; }
        public bool UseSystemTheme { get; set; }
        public bool EnableAnimations { get; set; }
        public bool RememberWindowPosition { get; set; }
        public bool MinimizeToTray { get; set; }
        public bool ShowNotifications { get; set; }
        public double CacheSize { get; set; }
        public int MaxConcurrentRequests { get; set; }
        public bool EnablePerformanceMonitoring { get; set; }
        public string LogLevel { get; set; }
        public bool EnableDebugMode { get; set; }
        public bool EnableTelemetry { get; set; }
    }
    
    #endregion
}
