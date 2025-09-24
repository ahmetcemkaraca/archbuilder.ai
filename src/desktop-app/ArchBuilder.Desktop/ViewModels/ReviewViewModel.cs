using System;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using System.Threading.Tasks;
using System.Windows.Input;
using System.Windows.Media;
using ArchBuilder.Desktop.Models;
using ArchBuilder.Desktop.Services;

namespace ArchBuilder.Desktop.ViewModels
{
    /// <summary>
    /// TR: Review window view model - validation sonuçlarını gözden geçirme ve onaylama
    /// </summary>
    public class ReviewViewModel : INotifyPropertyChanged
    {
        private readonly ApiClient _apiClient;
        private readonly LoggingService _loggingService;
        
        // TR: Review item data
        private string _reviewItemId;
        private string _reviewItemTitle;
        private string _reviewItemStatus;
        private string _reviewItemPriority;
        private DateTime _reviewItemCreatedDate;
        private string _reviewComments;
        
        // TR: Validation results
        private string _schemaValidationStatus;
        private string _geometricValidationStatus;
        private string _codeValidationStatus;
        private string _codeComplianceScore;
        
        // TR: Analysis results
        private string _geometryAnalysisSummary;
        private string _codeAnalysisSummary;
        private string _geometryConfidenceScore;
        private string _codeConfidenceScore;
        
        // TR: UI state
        private bool _canApprove;
        private bool _canReject;
        private bool _canRequestRevision;
        private bool _isLoading;
        
        public ReviewViewModel(ApiClient apiClient, LoggingService loggingService)
        {
            _apiClient = apiClient ?? throw new ArgumentNullException(nameof(apiClient));
            _loggingService = loggingService ?? throw new ArgumentNullException(nameof(loggingService));
            
            // TR: Initialize commands
            ApproveCommand = new RelayCommand(async () => await ApproveReview(), () => CanApprove && !IsLoading);
            RejectCommand = new RelayCommand(async () => await RejectReview(), () => CanReject && !IsLoading);
            RequestRevisionCommand = new RelayCommand(async () => await RequestRevision(), () => CanRequestRevision && !IsLoading);
            CloseCommand = new RelayCommand(() => CloseWindow());
            
            // TR: Initialize collections
            SchemaValidationErrors = new ObservableCollection<string>();
            GeometricValidationErrors = new ObservableCollection<string>();
            GeometricValidationWarnings = new ObservableCollection<string>();
            CodeValidationErrors = new ObservableCollection<string>();
            CodeValidationWarnings = new ObservableCollection<string>();
            Recommendations = new ObservableCollection<string>();
            ReviewHistory = new ObservableCollection<ReviewHistoryItem>();
            
            // TR: Initialize localized strings
            InitializeLocalizedStrings();
        }
        
        #region Properties
        
        // TR: Window title
        public string WindowTitle => GetLocalizedString("ReviewWindowTitle");
        
        // TR: Review item properties
        public string ReviewItemTitle
        {
            get => _reviewItemTitle;
            set => SetProperty(ref _reviewItemTitle, value);
        }
        
        public string ReviewItemStatus
        {
            get => _reviewItemStatus;
            set => SetProperty(ref _reviewItemStatus, value);
        }
        
        public string ReviewItemPriority
        {
            get => _reviewItemPriority;
            set => SetProperty(ref _reviewItemPriority, value);
        }
        
        public DateTime ReviewItemCreatedDate
        {
            get => _reviewItemCreatedDate;
            set => SetProperty(ref _reviewItemCreatedDate, value);
        }
        
        public string ReviewComments
        {
            get => _reviewComments;
            set => SetProperty(ref _reviewComments, value);
        }
        
        // TR: Validation status properties
        public string SchemaValidationStatus
        {
            get => _schemaValidationStatus;
            set => SetProperty(ref _schemaValidationStatus, value);
        }
        
        public string GeometricValidationStatus
        {
            get => _geometricValidationStatus;
            set => SetProperty(ref _geometricValidationStatus, value);
        }
        
        public string CodeValidationStatus
        {
            get => _codeValidationStatus;
            set => SetProperty(ref _codeValidationStatus, value);
        }
        
        public string CodeComplianceScore
        {
            get => _codeComplianceScore;
            set => SetProperty(ref _codeComplianceScore, value);
        }
        
        // TR: Analysis properties
        public string GeometryAnalysisSummary
        {
            get => _geometryAnalysisSummary;
            set => SetProperty(ref _geometryAnalysisSummary, value);
        }
        
        public string CodeAnalysisSummary
        {
            get => _codeAnalysisSummary;
            set => SetProperty(ref _codeAnalysisSummary, value);
        }
        
        public string GeometryConfidenceScore
        {
            get => _geometryConfidenceScore;
            set => SetProperty(ref _geometryConfidenceScore, value);
        }
        
        public string CodeConfidenceScore
        {
            get => _codeConfidenceScore;
            set => SetProperty(ref _codeConfidenceScore, value);
        }
        
        // TR: UI state properties
        public bool CanApprove
        {
            get => _canApprove;
            set => SetProperty(ref _canApprove, value);
        }
        
        public bool CanReject
        {
            get => _canReject;
            set => SetProperty(ref _canReject, value);
        }
        
        public bool CanRequestRevision
        {
            get => _canRequestRevision;
            set => SetProperty(ref _canRequestRevision, value);
        }
        
        public bool IsLoading
        {
            get => _isLoading;
            set => SetProperty(ref _isLoading, value);
        }
        
        // TR: Collections
        public ObservableCollection<string> SchemaValidationErrors { get; }
        public ObservableCollection<string> GeometricValidationErrors { get; }
        public ObservableCollection<string> GeometricValidationWarnings { get; }
        public ObservableCollection<string> CodeValidationErrors { get; }
        public ObservableCollection<string> CodeValidationWarnings { get; }
        public ObservableCollection<string> Recommendations { get; }
        public ObservableCollection<ReviewHistoryItem> ReviewHistory { get; }
        
        #endregion
        
        #region Color Properties
        
        public Brush StatusColor
        {
            get
            {
                return _reviewItemStatus?.ToLower() switch
                {
                    "pending" => Brushes.Orange,
                    "in_review" => Brushes.Blue,
                    "approved" => Brushes.Green,
                    "rejected" => Brushes.Red,
                    "needs_revision" => Brushes.Yellow,
                    _ => Brushes.Gray
                };
            }
        }
        
        public Brush PriorityColor
        {
            get
            {
                return _reviewItemPriority?.ToLower() switch
                {
                    "low" => Brushes.Green,
                    "medium" => Brushes.Orange,
                    "high" => Brushes.Red,
                    "critical" => Brushes.DarkRed,
                    _ => Brushes.Gray
                };
            }
        }
        
        public Brush SchemaValidationColor
        {
            get
            {
                return _schemaValidationStatus?.ToLower() switch
                {
                    "valid" or "success" => Brushes.Green,
                    "invalid" or "error" => Brushes.Red,
                    _ => Brushes.Gray
                };
            }
        }
        
        public Brush GeometricValidationColor
        {
            get
            {
                return _geometricValidationStatus?.ToLower() switch
                {
                    "valid" or "success" => Brushes.Green,
                    "invalid" or "error" => Brushes.Red,
                    _ => Brushes.Gray
                };
            }
        }
        
        public Brush CodeValidationColor
        {
            get
            {
                return _codeValidationStatus?.ToLower() switch
                {
                    "valid" or "success" => Brushes.Green,
                    "invalid" or "error" => Brushes.Red,
                    _ => Brushes.Gray
                };
            }
        }
        
        #endregion
        
        #region Localized Strings
        
        public string StatusLabel => GetLocalizedString("StatusLabel");
        public string PriorityLabel => GetLocalizedString("PriorityLabel");
        public string CreatedDateLabel => GetLocalizedString("CreatedDateLabel");
        public string ValidationResultsLabel => GetLocalizedString("ValidationResultsLabel");
        public string SchemaValidationLabel => GetLocalizedString("SchemaValidationLabel");
        public string GeometricValidationLabel => GetLocalizedString("GeometricValidationLabel");
        public string CodeValidationLabel => GetLocalizedString("CodeValidationLabel");
        public string ProjectAnalysisLabel => GetLocalizedString("ProjectAnalysisLabel");
        public string GeometryAnalysisLabel => GetLocalizedString("GeometryAnalysisLabel");
        public string CodeAnalysisLabel => GetLocalizedString("CodeAnalysisLabel");
        public string RecommendationsLabel => GetLocalizedString("RecommendationsLabel");
        public string ReviewHistoryLabel => GetLocalizedString("ReviewHistoryLabel");
        public string CommentsLabel => GetLocalizedString("CommentsLabel");
        public string ApproveButtonLabel => GetLocalizedString("ApproveButtonLabel");
        public string RejectButtonLabel => GetLocalizedString("RejectButtonLabel");
        public string RequestRevisionButtonLabel => GetLocalizedString("RequestRevisionButtonLabel");
        public string CloseButtonLabel => GetLocalizedString("CloseButtonLabel");
        
        #endregion
        
        #region Commands
        
        public ICommand ApproveCommand { get; }
        public ICommand RejectCommand { get; }
        public ICommand RequestRevisionCommand { get; }
        public ICommand CloseCommand { get; }
        
        #endregion
        
        #region Methods
        
        /// <summary>
        /// TR: Review item'ı yükle
        /// </summary>
        public async Task LoadReviewItemAsync(string reviewItemId)
        {
            try
            {
                IsLoading = true;
                _reviewItemId = reviewItemId;
                
                // TR: API'dan review item'ı getir
                var reviewItem = await _apiClient.GetReviewItemAsync(reviewItemId);
                if (reviewItem == null)
                {
                    _loggingService.LogError($"TR: Review item bulunamadı: {reviewItemId}");
                    return;
                }
                
                // TR: Review item verilerini yükle
                ReviewItemTitle = reviewItem.ItemType;
                ReviewItemStatus = reviewItem.Status;
                ReviewItemPriority = reviewItem.Priority;
                ReviewItemCreatedDate = reviewItem.CreatedAt;
                
                // TR: Validation sonuçlarını yükle
                LoadValidationResults(reviewItem.ItemData);
                
                // TR: Review history'yi yükle
                await LoadReviewHistoryAsync(reviewItemId);
                
                // TR: UI state'i güncelle
                UpdateUIState();
                
                _loggingService.LogInfo($"TR: Review item yüklendi: {reviewItemId}");
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Review item yükleme hatası: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }
        
        private void LoadValidationResults(dynamic itemData)
        {
            try
            {
                // TR: Schema validation
                if (itemData?.schema != null)
                {
                    SchemaValidationStatus = itemData.schema.success ? "Valid" : "Invalid";
                    if (itemData.schema.errors != null)
                    {
                        SchemaValidationErrors.Clear();
                        foreach (var error in itemData.schema.errors)
                        {
                            SchemaValidationErrors.Add(error.ToString());
                        }
                    }
                }
                
                // TR: Geometric validation
                if (itemData?.geometric != null)
                {
                    GeometricValidationStatus = itemData.geometric.success ? "Valid" : "Invalid";
                    if (itemData.geometric.data?.errors != null)
                    {
                        GeometricValidationErrors.Clear();
                        foreach (var error in itemData.geometric.data.errors)
                        {
                            GeometricValidationErrors.Add(error.ToString());
                        }
                    }
                    if (itemData.geometric.data?.warnings != null)
                    {
                        GeometricValidationWarnings.Clear();
                        foreach (var warning in itemData.geometric.data.warnings)
                        {
                            GeometricValidationWarnings.Add(warning.ToString());
                        }
                    }
                }
                
                // TR: Code validation
                if (itemData?.code != null)
                {
                    CodeValidationStatus = itemData.code.success ? "Valid" : "Invalid";
                    if (itemData.code.data?.code_compliance != null)
                    {
                        var compliance = itemData.code.data.code_compliance;
                        CodeComplianceScore = $"TR: Uyum Skoru: {compliance.compliance_score:P0}";
                    }
                    if (itemData.code.data?.errors != null)
                    {
                        CodeValidationErrors.Clear();
                        foreach (var error in itemData.code.data.errors)
                        {
                            CodeValidationErrors.Add(error.ToString());
                        }
                    }
                    if (itemData.code.data?.warnings != null)
                    {
                        CodeValidationWarnings.Clear();
                        foreach (var warning in itemData.code.data.warnings)
                        {
                            CodeValidationWarnings.Add(warning.ToString());
                        }
                    }
                }
                
                // TR: Analysis results
                if (itemData?.analysis != null)
                {
                    if (itemData.analysis.geometry_analysis != null)
                    {
                        var geoAnalysis = itemData.analysis.geometry_analysis;
                        GeometryAnalysisSummary = $"TR: {geoAnalysis.total_rooms} oda, {geoAnalysis.total_area}m²";
                        GeometryConfidenceScore = $"TR: Güven Skoru: {geoAnalysis.confidence_score:P0}";
                    }
                    
                    if (itemData.analysis.code_analysis != null)
                    {
                        var codeAnalysis = itemData.analysis.code_analysis;
                        CodeAnalysisSummary = $"TR: {codeAnalysis.compliance_score:P0} uyum";
                        CodeConfidenceScore = $"TR: Güven Skoru: {codeAnalysis.confidence_score:P0}";
                    }
                    
                    if (itemData.analysis.recommendations != null)
                    {
                        Recommendations.Clear();
                        foreach (var rec in itemData.analysis.recommendations)
                        {
                            Recommendations.Add(rec.ToString());
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Validation results yükleme hatası: {ex.Message}");
            }
        }
        
        private async Task LoadReviewHistoryAsync(string reviewItemId)
        {
            try
            {
                var history = await _apiClient.GetReviewHistoryAsync(reviewItemId);
                if (history != null)
                {
                    ReviewHistory.Clear();
                    foreach (var item in history)
                    {
                        ReviewHistory.Add(new ReviewHistoryItem
                        {
                            Action = item.Action,
                            Comment = item.Comment,
                            Reviewer = item.Reviewer,
                            Timestamp = item.Timestamp
                        });
                    }
                }
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Review history yükleme hatası: {ex.Message}");
            }
        }
        
        private void UpdateUIState()
        {
            // TR: UI state'i review status'a göre güncelle
            CanApprove = _reviewItemStatus?.ToLower() == "in_review";
            CanReject = _reviewItemStatus?.ToLower() == "in_review";
            CanRequestRevision = _reviewItemStatus?.ToLower() == "in_review";
            
            // TR: Color properties'leri güncelle
            OnPropertyChanged(nameof(StatusColor));
            OnPropertyChanged(nameof(PriorityColor));
            OnPropertyChanged(nameof(SchemaValidationColor));
            OnPropertyChanged(nameof(GeometricValidationColor));
            OnPropertyChanged(nameof(CodeValidationColor));
        }
        
        private async Task ApproveReview()
        {
            try
            {
                IsLoading = true;
                
                var result = await _apiClient.SubmitReviewAsync(_reviewItemId, "approved", ReviewComments);
                if (result.Success)
                {
                    _loggingService.LogInfo($"TR: Review onaylandı: {_reviewItemId}");
                    CloseWindow();
                }
                else
                {
                    _loggingService.LogError($"TR: Review onaylama hatası: {result.ErrorMessage}");
                }
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Review onaylama hatası: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }
        
        private async Task RejectReview()
        {
            try
            {
                IsLoading = true;
                
                var result = await _apiClient.SubmitReviewAsync(_reviewItemId, "rejected", ReviewComments);
                if (result.Success)
                {
                    _loggingService.LogInfo($"TR: Review reddedildi: {_reviewItemId}");
                    CloseWindow();
                }
                else
                {
                    _loggingService.LogError($"TR: Review reddetme hatası: {result.ErrorMessage}");
                }
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Review reddetme hatası: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }
        
        private async Task RequestRevision()
        {
            try
            {
                IsLoading = true;
                
                var feedbackData = new
                {
                    comments = ReviewComments,
                    requires_revision = true,
                    revision_areas = new[] { "geometry", "code" }
                };
                
                var result = await _apiClient.SubmitReviewAsync(_reviewItemId, "needs_revision", ReviewComments, feedbackData);
                if (result.Success)
                {
                    _loggingService.LogInfo($"TR: Review revision istendi: {_reviewItemId}");
                    CloseWindow();
                }
                else
                {
                    _loggingService.LogError($"TR: Review revision isteme hatası: {result.ErrorMessage}");
                }
            }
            catch (Exception ex)
            {
                _loggingService.LogError($"TR: Review revision isteme hatası: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
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
        
        private void InitializeLocalizedStrings()
        {
            // TR: Localized strings burada initialize edilecek
            // Şimdilik hardcoded değerler kullanıyoruz
        }
        
        private string GetLocalizedString(string key)
        {
            // TR: Localization service'den string getir
            // Şimdilik hardcoded değerler döndürüyoruz
            return key switch
            {
                "ReviewWindowTitle" => "TR: Review - Validation Sonuçları",
                "StatusLabel" => "TR: Durum:",
                "PriorityLabel" => "TR: Öncelik:",
                "CreatedDateLabel" => "TR: Oluşturulma:",
                "ValidationResultsLabel" => "TR: Validation Sonuçları",
                "SchemaValidationLabel" => "TR: Schema",
                "GeometricValidationLabel" => "TR: Geometri",
                "CodeValidationLabel" => "TR: Kod",
                "ProjectAnalysisLabel" => "TR: Proje Analizi",
                "GeometryAnalysisLabel" => "TR: Geometri Analizi",
                "CodeAnalysisLabel" => "TR: Kod Analizi",
                "RecommendationsLabel" => "TR: Öneriler",
                "ReviewHistoryLabel" => "TR: Review Geçmişi",
                "CommentsLabel" => "TR: Yorumlar:",
                "ApproveButtonLabel" => "TR: Onayla",
                "RejectButtonLabel" => "TR: Reddet",
                "RequestRevisionButtonLabel" => "TR: Revision İste",
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
    
    /// <summary>
    /// TR: Review history item model
    /// </summary>
    public class ReviewHistoryItem
    {
        public string Action { get; set; }
        public string Comment { get; set; }
        public string Reviewer { get; set; }
        public DateTime Timestamp { get; set; }
    }
    
    /// <summary>
    /// TR: Simple relay command implementation
    /// </summary>
    public class RelayCommand : ICommand
    {
        private readonly Action _execute;
        private readonly Func<bool> _canExecute;
        
        public RelayCommand(Action execute, Func<bool> canExecute = null)
        {
            _execute = execute ?? throw new ArgumentNullException(nameof(execute));
            _canExecute = canExecute;
        }
        
        public event EventHandler CanExecuteChanged
        {
            add { CommandManager.RequerySuggested += value; }
            remove { CommandManager.RequerySuggested -= value; }
        }
        
        public bool CanExecute(object parameter) => _canExecute?.Invoke() ?? true;
        
        public void Execute(object parameter) => _execute();
    }
}
