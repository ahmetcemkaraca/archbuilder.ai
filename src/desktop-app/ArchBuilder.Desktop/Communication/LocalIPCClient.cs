using System;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using ArchBuilder.Desktop.Core.Models;
using ArchBuilder.Desktop.Core.Interfaces;

namespace ArchBuilder.Desktop.Communication
{
    /// <summary>
    /// Local IPC client for communication between Desktop app and Revit plugin
    /// Supports both Named Pipes and HTTP communication protocols
    /// </summary>
    public class LocalIPCClient : ILocalIPCClient, IDisposable
    {
        private readonly ILogger<LocalIPCClient> _logger;
        private readonly LocalIPCConfiguration _config;
        private readonly JsonSerializerOptions _jsonOptions;
        private bool _disposed = false;

        public LocalIPCClient(ILogger<LocalIPCClient> logger, LocalIPCConfiguration config)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _config = config ?? throw new ArgumentNullException(nameof(config));
            
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                WriteIndented = false,
                DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
            };
        }

        #region Named Pipes Communication

        /// <summary>
        /// Send message via Named Pipes to Revit plugin
        /// </summary>
        public async Task<IPCResponse<T>> SendNamedPipeMessageAsync<T>(
            IPCMessage<T> message, 
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Sending Named Pipe message: {MessageType}", message.MessageType);
            
            try
            {
                using var pipeClient = new NamedPipeClientStream(
                    ".", 
                    _config.PipeName, 
                    PipeDirection.Out, 
                    PipeOptions.Asynchronous
                );

                await pipeClient.ConnectAsync(_config.PipeTimeoutMs, cancellationToken);
                
                var jsonMessage = JsonSerializer.Serialize(message, _jsonOptions);
                var messageBytes = Encoding.UTF8.GetBytes(jsonMessage);
                
                // Send message length first
                var lengthBytes = BitConverter.GetBytes(messageBytes.Length);
                await pipeClient.WriteAsync(lengthBytes, 0, lengthBytes.Length, cancellationToken);
                
                // Send message content
                await pipeClient.WriteAsync(messageBytes, 0, messageBytes.Length, cancellationToken);
                await pipeClient.FlushAsync(cancellationToken);
                
                _logger.LogInformation("Named Pipe message sent successfully: {MessageType}", message.MessageType);
                
                return new IPCResponse<T>
                {
                    Success = true,
                    MessageType = message.MessageType,
                    CorrelationId = message.CorrelationId,
                    Timestamp = DateTime.UtcNow
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to send Named Pipe message: {MessageType}", message.MessageType);
                return new IPCResponse<T>
                {
                    Success = false,
                    MessageType = message.MessageType,
                    CorrelationId = message.CorrelationId,
                    Error = ex.Message,
                    Timestamp = DateTime.UtcNow
                };
            }
        }

        /// <summary>
        /// Listen for Named Pipe messages from Revit plugin
        /// </summary>
        public async Task<IPCResponse<T>> ListenForNamedPipeMessageAsync<T>(
            string expectedMessageType,
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Listening for Named Pipe message: {MessageType}", expectedMessageType);
            
            try
            {
                using var pipeServer = new NamedPipeServerStream(
                    _config.PipeName,
                    PipeDirection.In,
                    1,
                    PipeTransmissionMode.Byte,
                    PipeOptions.Asynchronous
                );

                await pipeServer.WaitForConnectionAsync(cancellationToken);
                
                // Read message length
                var lengthBytes = new byte[4];
                await pipeServer.ReadAsync(lengthBytes, 0, 4, cancellationToken);
                var messageLength = BitConverter.ToInt32(lengthBytes, 0);
                
                // Read message content
                var messageBytes = new byte[messageLength];
                var totalBytesRead = 0;
                
                while (totalBytesRead < messageLength)
                {
                    var bytesRead = await pipeServer.ReadAsync(
                        messageBytes, 
                        totalBytesRead, 
                        messageLength - totalBytesRead, 
                        cancellationToken
                    );
                    totalBytesRead += bytesRead;
                }
                
                var jsonMessage = Encoding.UTF8.GetString(messageBytes);
                var message = JsonSerializer.Deserialize<IPCMessage<T>>(jsonMessage, _jsonOptions);
                
                if (message.MessageType != expectedMessageType)
                {
                    throw new InvalidOperationException(
                        $"Expected message type '{expectedMessageType}', but received '{message.MessageType}'"
                    );
                }
                
                _logger.LogInformation("Named Pipe message received successfully: {MessageType}", message.MessageType);
                
                return new IPCResponse<T>
                {
                    Success = true,
                    MessageType = message.MessageType,
                    CorrelationId = message.CorrelationId,
                    Data = message.Data,
                    Timestamp = DateTime.UtcNow
                };
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to receive Named Pipe message: {MessageType}", expectedMessageType);
                return new IPCResponse<T>
                {
                    Success = false,
                    MessageType = expectedMessageType,
                    Error = ex.Message,
                    Timestamp = DateTime.UtcNow
                };
            }
        }

        #endregion

        #region HTTP Communication

        /// <summary>
        /// Send HTTP request to local cloud server
        /// </summary>
        public async Task<IPCResponse<T>> SendHttpRequestAsync<T>(
            string endpoint,
            object requestData,
            string correlationId,
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Sending HTTP request to: {Endpoint}", endpoint);
            
            try
            {
                using var httpClient = new System.Net.Http.HttpClient();
                httpClient.Timeout = TimeSpan.FromMilliseconds(_config.HttpTimeoutMs);
                
                var jsonContent = JsonSerializer.Serialize(requestData, _jsonOptions);
                var content = new StringContent(jsonContent, Encoding.UTF8, "application/json");
                
                // Add correlation ID header
                content.Headers.Add("X-Correlation-ID", correlationId);
                
                var response = await httpClient.PostAsync(
                    $"{_config.LocalServerUrl}{endpoint}",
                    content,
                    cancellationToken
                );
                
                var responseContent = await response.Content.ReadAsStringAsync(cancellationToken);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseData = JsonSerializer.Deserialize<T>(responseContent, _jsonOptions);
                    
                    _logger.LogInformation("HTTP request completed successfully: {Endpoint}", endpoint);
                    
                    return new IPCResponse<T>
                    {
                        Success = true,
                        CorrelationId = correlationId,
                        Data = responseData,
                        Timestamp = DateTime.UtcNow
                    };
                }
                else
                {
                    _logger.LogWarning("HTTP request failed: {StatusCode} - {Content}", 
                        response.StatusCode, responseContent);
                    
                    return new IPCResponse<T>
                    {
                        Success = false,
                        CorrelationId = correlationId,
                        Error = $"HTTP {response.StatusCode}: {responseContent}",
                        Timestamp = DateTime.UtcNow
                    };
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to send HTTP request: {Endpoint}", endpoint);
                return new IPCResponse<T>
                {
                    Success = false,
                    CorrelationId = correlationId,
                    Error = ex.Message,
                    Timestamp = DateTime.UtcNow
                };
            }
        }

        /// <summary>
        /// Send AI command to cloud server via HTTP
        /// </summary>
        public async Task<IPCResponse<AICommandResponse>> SendAICommandAsync(
            AICommandRequest request,
            CancellationToken cancellationToken = default)
        {
            return await SendHttpRequestAsync<AICommandResponse>(
                "/v1/ai/commands",
                request,
                request.CorrelationId,
                cancellationToken
            );
        }

        /// <summary>
        /// Send project analysis request to cloud server
        /// </summary>
        public async Task<IPCResponse<ProjectAnalysisResponse>> SendProjectAnalysisAsync(
            ProjectAnalysisRequest request,
            CancellationToken cancellationToken = default)
        {
            return await SendHttpRequestAsync<ProjectAnalysisResponse>(
                "/v1/validation/analyze/project",
                request,
                request.CorrelationId,
                cancellationToken
            );
        }

        #endregion

        #region Health Check

        /// <summary>
        /// Check if local cloud server is available
        /// </summary>
        public async Task<bool> IsLocalServerAvailableAsync(CancellationToken cancellationToken = default)
        {
            try
            {
                using var httpClient = new System.Net.Http.HttpClient();
                httpClient.Timeout = TimeSpan.FromMilliseconds(_config.HttpTimeoutMs);
                
                var response = await httpClient.GetAsync(
                    $"{_config.LocalServerUrl}/health",
                    cancellationToken
                );
                
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Local server health check failed");
                return false;
            }
        }

        /// <summary>
        /// Check if Revit plugin is available via Named Pipes
        /// </summary>
        public async Task<bool> IsRevitPluginAvailableAsync(CancellationToken cancellationToken = default)
        {
            try
            {
                using var pipeClient = new NamedPipeClientStream(
                    ".",
                    _config.PipeName,
                    PipeDirection.Out
                );

                await pipeClient.ConnectAsync(_config.PipeTimeoutMs, cancellationToken);
                return pipeClient.IsConnected;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Revit plugin availability check failed");
                return false;
            }
        }

        #endregion

        #region Message Contracts

        /// <summary>
        /// Send layout generation request to Revit plugin
        /// </summary>
        public async Task<IPCResponse<LayoutGenerationResponse>> SendLayoutGenerationRequestAsync(
            LayoutGenerationRequest request,
            CancellationToken cancellationToken = default)
        {
            var message = new IPCMessage<LayoutGenerationRequest>
            {
                MessageType = "layout_generation_request",
                CorrelationId = request.CorrelationId,
                Data = request,
                Timestamp = DateTime.UtcNow
            };

            return await SendNamedPipeMessageAsync(message, cancellationToken);
        }

        /// <summary>
        /// Send validation request to Revit plugin
        /// </summary>
        public async Task<IPCResponse<ValidationResponse>> SendValidationRequestAsync(
            ValidationRequest request,
            CancellationToken cancellationToken = default)
        {
            var message = new IPCMessage<ValidationRequest>
            {
                MessageType = "validation_request",
                CorrelationId = request.CorrelationId,
                Data = request,
                Timestamp = DateTime.UtcNow
            };

            return await SendNamedPipeMessageAsync(message, cancellationToken);
        }

        /// <summary>
        /// Listen for progress updates from Revit plugin
        /// </summary>
        public async Task<IPCResponse<ProgressUpdate>> ListenForProgressUpdateAsync(
            CancellationToken cancellationToken = default)
        {
            return await ListenForNamedPipeMessageAsync<ProgressUpdate>(
                "progress_update",
                cancellationToken
            );
        }

        /// <summary>
        /// Listen for completion notifications from Revit plugin
        /// </summary>
        public async Task<IPCResponse<CompletionNotification>> ListenForCompletionAsync(
            CancellationToken cancellationToken = default)
        {
            return await ListenForNamedPipeMessageAsync<CompletionNotification>(
                "completion_notification",
                cancellationToken
            );
        }

        #endregion

        #region IDisposable

        public void Dispose()
        {
            Dispose(true);
            GC.SuppressFinalize(this);
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_disposed && disposing)
            {
                _logger.LogInformation("Disposing LocalIPCClient");
                _disposed = true;
            }
        }

        #endregion
    }

    /// <summary>
    /// Configuration for Local IPC communication
    /// </summary>
    public class LocalIPCConfiguration
    {
        public string PipeName { get; set; } = "ArchBuilderIPC";
        public int PipeTimeoutMs { get; set; } = 5000;
        public string LocalServerUrl { get; set; } = "http://localhost:8000";
        public int HttpTimeoutMs { get; set; } = 30000;
        public int RetryAttempts { get; set; } = 3;
        public int RetryDelayMs { get; set; } = 1000;
    }

    /// <summary>
    /// Base interface for Local IPC communication
    /// </summary>
    public interface ILocalIPCClient : IDisposable
    {
        Task<IPCResponse<T>> SendNamedPipeMessageAsync<T>(
            IPCMessage<T> message, 
            CancellationToken cancellationToken = default);
        
        Task<IPCResponse<T>> ListenForNamedPipeMessageAsync<T>(
            string expectedMessageType,
            CancellationToken cancellationToken = default);
        
        Task<IPCResponse<T>> SendHttpRequestAsync<T>(
            string endpoint,
            object requestData,
            string correlationId,
            CancellationToken cancellationToken = default);
        
        Task<bool> IsLocalServerAvailableAsync(CancellationToken cancellationToken = default);
        Task<bool> IsRevitPluginAvailableAsync(CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Generic IPC message wrapper
    /// </summary>
    public class IPCMessage<T>
    {
        public string MessageType { get; set; }
        public string CorrelationId { get; set; }
        public T Data { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Generic IPC response wrapper
    /// </summary>
    public class IPCResponse<T>
    {
        public bool Success { get; set; }
        public string MessageType { get; set; }
        public string CorrelationId { get; set; }
        public T Data { get; set; }
        public string Error { get; set; }
        public DateTime Timestamp { get; set; }
    }
}
