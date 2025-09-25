using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Pipes;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Service for local communication between Revit plugin and desktop app
    /// Supports both Named Pipes and HTTP communication
    /// </summary>
    public class LocalCommunicationService : ILocalCommunicationService
    {
        private readonly ILogger<LocalCommunicationService> _logger;
        private readonly IConfigurationHelper _configHelper;
        private readonly HttpClient _httpClient;
        private readonly string _pipeName;
        private readonly int _httpPort;
        private readonly string _baseUrl;
        private readonly int _timeoutSeconds;
        private bool _disposed = false;

        public LocalCommunicationService(
            ILogger<LocalCommunicationService> logger,
            IConfigurationHelper configHelper,
            HttpClient httpClient)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _configHelper = configHelper ?? throw new ArgumentNullException(nameof(configHelper));
            _httpClient = httpClient ?? throw new ArgumentNullException(nameof(httpClient));

            _pipeName = _configHelper.GetString("LocalCommunication:PipeName", "ArchBuilderRevitPipe");
            _httpPort = _configHelper.GetInt("LocalCommunication:HttpPort", 8080);
            _baseUrl = $"http://localhost:{_httpPort}";
            _timeoutSeconds = _configHelper.GetInt("LocalCommunication:ConnectionTimeoutSeconds", 30);
        }

        /// <summary>
        /// Initialize the communication service
        /// </summary>
        public async Task<bool> InitializeAsync(string correlationId)
        {
            using var scope = _logger.BeginScope("InitializeAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Initializing local communication service");

                // Test both communication methods
                var pipeAvailable = await TestNamedPipeConnectionAsync();
                var httpAvailable = await TestHttpConnectionAsync();

                if (pipeAvailable)
                {
                    _logger.LogInformation("Named pipe communication available");
                }
                else if (httpAvailable)
                {
                    _logger.LogInformation("HTTP communication available");
                }
                else
                {
                    _logger.LogWarning("No communication method available");
                    return false;
                }

                _logger.LogInformation("Local communication service initialized successfully");
                return true;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error initializing local communication service");
                return false;
            }
        }

        /// <summary>
        /// Send message to desktop app
        /// </summary>
        public async Task<bool> SendMessageAsync(CommunicationMessage message, string correlationId)
        {
            if (message == null)
                throw new ArgumentNullException(nameof(message));

            using var scope = _logger.BeginScope("SendMessageAsync {MessageType} {CorrelationId}", message.Type, correlationId);

            try
            {
                _logger.LogDebug("Sending message of type {MessageType}", message.Type);

                // Try Named Pipes first, fallback to HTTP
                var success = await SendMessageViaNamedPipeAsync(message) ||
                             await SendMessageViaHttpAsync(message);

                if (success)
                {
                    _logger.LogDebug("Message sent successfully");
                }
                else
                {
                    _logger.LogError("Failed to send message via any communication method");
                }

                return success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending message");
                return false;
            }
        }

        /// <summary>
        /// Receive message from desktop app
        /// </summary>
        public async Task<CommunicationMessage> ReceiveMessageAsync(string correlationId)
        {
            using var scope = _logger.BeginScope("ReceiveMessageAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogDebug("Receiving message");

                // Try Named Pipes first, fallback to HTTP
                var message = await ReceiveMessageViaNamedPipeAsync() ??
                             await ReceiveMessageViaHttpAsync();

                if (message != null)
                {
                    _logger.LogDebug("Message received successfully: {MessageType}", message.Type);
                }
                else
                {
                    _logger.LogWarning("No message received within timeout");
                }

                return message;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error receiving message");
                return null;
            }
        }

        /// <summary>
        /// Send project analysis data to desktop app
        /// </summary>
        public async Task<bool> SendProjectAnalysisAsync(ProjectAnalysisResult analysisData, string correlationId)
        {
            if (analysisData == null)
                throw new ArgumentNullException(nameof(analysisData));

            using var scope = _logger.BeginScope("SendProjectAnalysisAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Sending project analysis data");

                var message = new CommunicationMessage
                {
                    Id = Guid.NewGuid().ToString(),
                    Type = MessageTypes.PROJECT_ANALYSIS,
                    CorrelationId = correlationId,
                    Timestamp = DateTime.UtcNow,
                    Payload = analysisData
                };

                var success = await SendMessageAsync(message, correlationId);

                if (success)
                {
                    _logger.LogInformation("Project analysis data sent successfully");
                }
                else
                {
                    _logger.LogError("Failed to send project analysis data");
                }

                return success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending project analysis data");
                return false;
            }
        }

        /// <summary>
        /// Send layout generation request to desktop app
        /// </summary>
        public async Task<bool> SendLayoutRequestAsync(LayoutGenerationRequest layoutRequest, string correlationId)
        {
            if (layoutRequest == null)
                throw new ArgumentNullException(nameof(layoutRequest));

            using var scope = _logger.BeginScope("SendLayoutRequestAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Sending layout generation request");

                var message = new CommunicationMessage
                {
                    Id = Guid.NewGuid().ToString(),
                    Type = MessageTypes.LAYOUT_REQUEST,
                    CorrelationId = correlationId,
                    Timestamp = DateTime.UtcNow,
                    Payload = layoutRequest
                };

                var success = await SendMessageAsync(message, correlationId);

                if (success)
                {
                    _logger.LogInformation("Layout generation request sent successfully");
                }
                else
                {
                    _logger.LogError("Failed to send layout generation request");
                }

                return success;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error sending layout generation request");
                return false;
            }
        }

        /// <summary>
        /// Receive layout generation response from desktop app
        /// </summary>
        public async Task<LayoutGenerationResponse> ReceiveLayoutResponseAsync(string correlationId)
        {
            using var scope = _logger.BeginScope("ReceiveLayoutResponseAsync {CorrelationId}", correlationId);

            try
            {
                _logger.LogInformation("Receiving layout generation response");

                var message = await ReceiveMessageAsync(correlationId);
                if (message?.Type == MessageTypes.LAYOUT_RESPONSE)
                {
                    var response = JsonConvert.DeserializeObject<LayoutGenerationResponse>(
                        JsonConvert.SerializeObject(message.Payload));
                    
                    _logger.LogInformation("Layout generation response received successfully");
                    return response;
                }

                _logger.LogWarning("No layout response received or invalid message type");
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error receiving layout generation response");
                return null;
            }
        }

        /// <summary>
        /// Check if desktop app is available
        /// </summary>
        public async Task<bool> IsDesktopAppAvailableAsync()
        {
            try
            {
                return await TestNamedPipeConnectionAsync() || await TestHttpConnectionAsync();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error checking desktop app availability");
                return false;
            }
        }

        /// <summary>
        /// Dispose the communication service
        /// </summary>
        public void Dispose()
        {
            if (!_disposed)
            {
                try
                {
                    _httpClient?.Dispose();
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error disposing communication service");
                }
                finally
                {
                    _disposed = true;
                }
            }
        }

        #region Private Helper Methods

        private async Task<bool> TestNamedPipeConnectionAsync()
        {
            try
            {
                using var pipeClient = new NamedPipeClientStream(".", _pipeName, PipeDirection.Out);
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
                
                await pipeClient.ConnectAsync(cts.Token);
                return pipeClient.IsConnected;
            }
            catch
            {
                return false;
            }
        }

        private async Task<bool> TestHttpConnectionAsync()
        {
            try
            {
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(5));
                var response = await _httpClient.GetAsync($"{_baseUrl}/health", cts.Token);
                return response.IsSuccessStatusCode;
            }
            catch
            {
                return false;
            }
        }

        private async Task<bool> SendMessageViaNamedPipeAsync(CommunicationMessage message)
        {
            try
            {
                using var pipeClient = new NamedPipeClientStream(".", _pipeName, PipeDirection.Out);
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_timeoutSeconds));
                
                await pipeClient.ConnectAsync(cts.Token);
                
                if (pipeClient.IsConnected)
                {
                    var json = JsonConvert.SerializeObject(message);
                    var data = Encoding.UTF8.GetBytes(json);
                    await pipeClient.WriteAsync(data, 0, data.Length);
                    return true;
                }
                
                return false;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Named pipe communication failed");
                return false;
            }
        }

        private async Task<bool> SendMessageViaHttpAsync(CommunicationMessage message)
        {
            try
            {
                var json = JsonConvert.SerializeObject(message);
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_timeoutSeconds));
                var response = await _httpClient.PostAsync($"{_baseUrl}/api/messages", content, cts.Token);
                
                return response.IsSuccessStatusCode;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "HTTP communication failed");
                return false;
            }
        }

        private async Task<CommunicationMessage> ReceiveMessageViaNamedPipeAsync()
        {
            try
            {
                using var pipeClient = new NamedPipeClientStream(".", _pipeName, PipeDirection.In);
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_timeoutSeconds));
                
                await pipeClient.ConnectAsync(cts.Token);
                
                if (pipeClient.IsConnected)
                {
                    var buffer = new byte[1024 * 1024]; // 1MB buffer
                    var bytesRead = await pipeClient.ReadAsync(buffer, 0, buffer.Length);
                    
                    if (bytesRead > 0)
                    {
                        var json = Encoding.UTF8.GetString(buffer, 0, bytesRead);
                        return JsonConvert.DeserializeObject<CommunicationMessage>(json);
                    }
                }
                
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "Named pipe receive failed");
                return null;
            }
        }

        private async Task<CommunicationMessage> ReceiveMessageViaHttpAsync()
        {
            try
            {
                using var cts = new CancellationTokenSource(TimeSpan.FromSeconds(_timeoutSeconds));
                var response = await _httpClient.GetAsync($"{_baseUrl}/api/messages", cts.Token);
                
                if (response.IsSuccessStatusCode)
                {
                    var json = await response.Content.ReadAsStringAsync();
                    return JsonConvert.DeserializeObject<CommunicationMessage>(json);
                }
                
                return null;
            }
            catch (Exception ex)
            {
                _logger.LogDebug(ex, "HTTP receive failed");
                return null;
            }
        }

        #endregion
    }
}
