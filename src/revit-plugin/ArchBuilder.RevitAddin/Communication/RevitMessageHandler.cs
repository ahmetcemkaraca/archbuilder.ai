using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using ArchBuilder.RevitAddin.Core.Interfaces;
using ArchBuilder.RevitAddin.Core.Models;

namespace ArchBuilder.RevitAddin.Communication
{
    /// <summary>
    /// Message handler for Revit plugin IPC communication
    /// Routes messages to appropriate Revit operations
    /// </summary>
    public class RevitMessageHandler : IMessageHandler
    {
        private readonly ILogger<RevitMessageHandler> _logger;
        private readonly ILayoutGenerationService _layoutService;
        private readonly IValidationService _validationService;
        private readonly IProjectAnalysisService _projectAnalysisService;

        public RevitMessageHandler(
            ILogger<RevitMessageHandler> logger,
            ILayoutGenerationService layoutService,
            IValidationService validationService,
            IProjectAnalysisService projectAnalysisService)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _layoutService = layoutService ?? throw new ArgumentNullException(nameof(layoutService));
            _validationService = validationService ?? throw new ArgumentNullException(nameof(validationService));
            _projectAnalysisService = projectAnalysisService ?? throw new ArgumentNullException(nameof(projectAnalysisService));
        }

        public async Task<IPCResponse<object>> HandleMessageAsync(
            IPCMessage<object> message, 
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Handling message: {MessageType}", message.MessageType);

            try
            {
                return message.MessageType switch
                {
                    "layout_generation_request" => await HandleLayoutGenerationRequestAsync(message, cancellationToken),
                    "validation_request" => await HandleValidationRequestAsync(message, cancellationToken),
                    "project_analysis_request" => await HandleProjectAnalysisRequestAsync(message, cancellationToken),
                    "health_check" => await HandleHealthCheckAsync(message, cancellationToken),
                    _ => CreateErrorResponse(message, $"Unknown message type: {message.MessageType}")
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error handling message: {MessageType}", message.MessageType);
                return CreateErrorResponse(message, ex.Message);
            }
        }

        #region Message Handlers

        private async Task<IPCResponse<object>> HandleLayoutGenerationRequestAsync(
            IPCMessage<object> message, 
            CancellationToken cancellationToken)
        {
            _logger.LogInformation("Handling layout generation request: {CorrelationId}", message.CorrelationId);

            try
            {
                // Deserialize the specific request type
                var requestJson = System.Text.Json.JsonSerializer.Serialize(message.Data);
                var request = System.Text.Json.JsonSerializer.Deserialize<LayoutGenerationRequest>(requestJson);

                // Execute layout generation
                var result = await _layoutService.GenerateLayoutAsync(request, cancellationToken);

                return new IPCResponse<object>
                {
                    Success = true,
                    MessageType = "layout_generation_response",
                    CorrelationId = message.CorrelationId,
                    Data = result,
                    Timestamp = DateTime.UtcNow
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in layout generation request: {CorrelationId}", message.CorrelationId);
                return CreateErrorResponse(message, ex.Message);
            }
        }

        private async Task<IPCResponse<object>> HandleValidationRequestAsync(
            IPCMessage<object> message, 
            CancellationToken cancellationToken)
        {
            _logger.LogInformation("Handling validation request: {CorrelationId}", message.CorrelationId);

            try
            {
                // Deserialize the specific request type
                var requestJson = System.Text.Json.JsonSerializer.Serialize(message.Data);
                var request = System.Text.Json.JsonSerializer.Deserialize<ValidationRequest>(requestJson);

                // Execute validation
                var result = await _validationService.ValidateAsync(request, cancellationToken);

                return new IPCResponse<object>
                {
                    Success = true,
                    MessageType = "validation_response",
                    CorrelationId = message.CorrelationId,
                    Data = result,
                    Timestamp = DateTime.UtcNow
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in validation request: {CorrelationId}", message.CorrelationId);
                return CreateErrorResponse(message, ex.Message);
            }
        }

        private async Task<IPCResponse<object>> HandleProjectAnalysisRequestAsync(
            IPCMessage<object> message, 
            CancellationToken cancellationToken)
        {
            _logger.LogInformation("Handling project analysis request: {CorrelationId}", message.CorrelationId);

            try
            {
                // Deserialize the specific request type
                var requestJson = System.Text.Json.JsonSerializer.Serialize(message.Data);
                var request = System.Text.Json.JsonSerializer.Deserialize<ProjectAnalysisRequest>(requestJson);

                // Execute project analysis
                var result = await _projectAnalysisService.AnalyzeProjectAsync(request, cancellationToken);

                return new IPCResponse<object>
                {
                    Success = true,
                    MessageType = "project_analysis_response",
                    CorrelationId = message.CorrelationId,
                    Data = result,
                    Timestamp = DateTime.UtcNow
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in project analysis request: {CorrelationId}", message.CorrelationId);
                return CreateErrorResponse(message, ex.Message);
            }
        }

        private async Task<IPCResponse<object>> HandleHealthCheckAsync(
            IPCMessage<object> message, 
            CancellationToken cancellationToken)
        {
            _logger.LogDebug("Handling health check request: {CorrelationId}", message.CorrelationId);

            try
            {
                // Perform health check
                var healthStatus = await PerformHealthCheckAsync(cancellationToken);

                return new IPCResponse<object>
                {
                    Success = true,
                    MessageType = "health_check_response",
                    CorrelationId = message.CorrelationId,
                    Data = healthStatus,
                    Timestamp = DateTime.UtcNow
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error in health check request: {CorrelationId}", message.CorrelationId);
                return CreateErrorResponse(message, ex.Message);
            }
        }

        #endregion

        #region Helper Methods

        private async Task<object> PerformHealthCheckAsync(CancellationToken cancellationToken)
        {
            // Check if Revit is available and responsive
            var isRevitAvailable = await CheckRevitAvailabilityAsync(cancellationToken);
            var isPluginLoaded = await CheckPluginStatusAsync(cancellationToken);
            var memoryUsage = await GetMemoryUsageAsync(cancellationToken);

            return new
            {
                Status = "healthy",
                RevitAvailable = isRevitAvailable,
                PluginLoaded = isPluginLoaded,
                MemoryUsageMB = memoryUsage,
                Timestamp = DateTime.UtcNow
            };
        }

        private async Task<bool> CheckRevitAvailabilityAsync(CancellationToken cancellationToken)
        {
            try
            {
                // Check if Revit API is accessible
                // This would typically involve checking if Revit.Application is available
                await Task.Delay(100, cancellationToken); // Simulate check
                return true;
            }
            catch
            {
                return false;
            }
        }

        private async Task<bool> CheckPluginStatusAsync(CancellationToken cancellationToken)
        {
            try
            {
                // Check if plugin services are loaded and functional
                await Task.Delay(50, cancellationToken); // Simulate check
                return _layoutService != null && _validationService != null;
            }
            catch
            {
                return false;
            }
        }

        private async Task<long> GetMemoryUsageAsync(CancellationToken cancellationToken)
        {
            try
            {
                await Task.Delay(10, cancellationToken); // Simulate check
                return GC.GetTotalMemory(false) / (1024 * 1024); // Convert to MB
            }
            catch
            {
                return 0;
            }
        }

        private IPCResponse<object> CreateErrorResponse(IPCMessage<object> message, string error)
        {
            return new IPCResponse<object>
            {
                Success = false,
                MessageType = $"{message.MessageType}_error",
                CorrelationId = message.CorrelationId,
                Error = error,
                Timestamp = DateTime.UtcNow
            };
        }

        #endregion
    }

    /// <summary>
    /// Layout generation request model
    /// </summary>
    public class LayoutGenerationRequest
    {
        public string CorrelationId { get; set; }
        public string UserPrompt { get; set; }
        public double TotalAreaM2 { get; set; }
        public string BuildingType { get; set; }
        public string Language { get; set; }
        public List<string> Requirements { get; set; } = new();
        public List<string> Constraints { get; set; } = new();
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Layout generation response model
    /// </summary>
    public class LayoutGenerationResponse
    {
        public string CorrelationId { get; set; }
        public bool Success { get; set; }
        public LayoutData LayoutData { get; set; }
        public List<RevitCommand> RevitCommands { get; set; } = new();
        public ValidationResult Validation { get; set; }
        public string Error { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Validation request model
    /// </summary>
    public class ValidationRequest
    {
        public string CorrelationId { get; set; }
        public object Payload { get; set; }
        public string BuildingType { get; set; }
        public string ValidationType { get; set; } // "geometric", "code", "both"
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Validation response model
    /// </summary>
    public class ValidationResponse
    {
        public string CorrelationId { get; set; }
        public bool Success { get; set; }
        public bool IsValid { get; set; }
        public List<ValidationError> Errors { get; set; } = new();
        public List<ValidationWarning> Warnings { get; set; } = new();
        public double ConfidenceScore { get; set; }
        public string Error { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Project analysis request model
    /// </summary>
    public class ProjectAnalysisRequest
    {
        public string CorrelationId { get; set; }
        public string ProjectId { get; set; }
        public string AnalysisType { get; set; } // "geometry", "code", "both"
        public Dictionary<string, object> Options { get; set; } = new();
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Project analysis response model
    /// </summary>
    public class ProjectAnalysisResponse
    {
        public string CorrelationId { get; set; }
        public bool Success { get; set; }
        public ProjectAnalysisData AnalysisData { get; set; }
        public List<Recommendation> Recommendations { get; set; } = new();
        public double ConfidenceScore { get; set; }
        public string Error { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Layout data model
    /// </summary>
    public class LayoutData
    {
        public List<RoomDefinition> Rooms { get; set; } = new();
        public List<WallDefinition> Walls { get; set; } = new();
        public List<DoorDefinition> Doors { get; set; } = new();
        public List<WindowDefinition> Windows { get; set; } = new();
        public CirculationData Circulation { get; set; }
    }

    /// <summary>
    /// Revit command model
    /// </summary>
    public class RevitCommand
    {
        public string CommandType { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new();
        public int ExecutionOrder { get; set; }
        public string Description { get; set; }
    }

    /// <summary>
    /// Validation error model
    /// </summary>
    public class ValidationError
    {
        public string Code { get; set; }
        public string Message { get; set; }
        public string Property { get; set; }
        public object AttemptedValue { get; set; }
        public string Severity { get; set; }
        public List<string> SuggestedFixes { get; set; } = new();
    }

    /// <summary>
    /// Validation warning model
    /// </summary>
    public class ValidationWarning
    {
        public string Code { get; set; }
        public string Message { get; set; }
        public string Property { get; set; }
        public string Severity { get; set; }
    }

    /// <summary>
    /// Project analysis data model
    /// </summary>
    public class ProjectAnalysisData
    {
        public GeometryAnalysis GeometryAnalysis { get; set; }
        public CodeAnalysis CodeAnalysis { get; set; }
        public PerformanceMetrics PerformanceMetrics { get; set; }
    }

    /// <summary>
    /// Recommendation model
    /// </summary>
    public class Recommendation
    {
        public string Category { get; set; }
        public string Title { get; set; }
        public string Description { get; set; }
        public string Priority { get; set; }
        public string Implementation { get; set; }
        public double Impact { get; set; }
    }
}
