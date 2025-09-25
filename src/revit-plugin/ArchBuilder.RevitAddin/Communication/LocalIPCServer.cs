using System;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using ArchBuilder.RevitAddin.Core.Models;
using ArchBuilder.RevitAddin.Core.Interfaces;

namespace ArchBuilder.RevitAddin.Communication
{
    /// <summary>
    /// Local IPC server for communication between Revit plugin and Desktop app
    /// Handles Named Pipes communication and message routing
    /// </summary>
    public class LocalIPCServer : ILocalIPCServer, IDisposable
    {
        private readonly ILogger<LocalIPCServer> _logger;
        private readonly LocalIPCConfiguration _config;
        private readonly IMessageHandler _messageHandler;
        private readonly JsonSerializerOptions _jsonOptions;
        private CancellationTokenSource _cancellationTokenSource;
        private Task _serverTask;
        private bool _disposed = false;

        public LocalIPCServer(
            ILogger<LocalIPCServer> logger, 
            LocalIPCConfiguration config,
            IMessageHandler messageHandler)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
            _config = config ?? throw new ArgumentNullException(nameof(config));
            _messageHandler = messageHandler ?? throw new ArgumentNullException(nameof(messageHandler));
            
            _jsonOptions = new JsonSerializerOptions
            {
                PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                WriteIndented = false,
                DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull
            };
        }

        #region Server Management

        /// <summary>
        /// Start the Named Pipes server
        /// </summary>
        public async Task StartAsync(CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Starting Local IPC Server with pipe name: {PipeName}", _config.PipeName);
            
            _cancellationTokenSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            _serverTask = Task.Run(() => RunServerAsync(_cancellationTokenSource.Token), _cancellationTokenSource.Token);
            
            await Task.CompletedTask;
        }

        /// <summary>
        /// Stop the Named Pipes server
        /// </summary>
        public async Task StopAsync()
        {
            _logger.LogInformation("Stopping Local IPC Server");
            
            _cancellationTokenSource?.Cancel();
            
            if (_serverTask != null)
            {
                try
                {
                    await _serverTask;
                }
                catch (OperationCanceledException)
                {
                    // Expected when stopping
                }
            }
            
            _cancellationTokenSource?.Dispose();
        }

        /// <summary>
        /// Main server loop
        /// </summary>
        private async Task RunServerAsync(CancellationToken cancellationToken)
        {
            _logger.LogInformation("Local IPC Server started");
            
            while (!cancellationToken.IsCancellationRequested)
            {
                try
                {
                    await HandleClientConnectionAsync(cancellationToken);
                }
                catch (OperationCanceledException)
                {
                    _logger.LogInformation("Local IPC Server stopped");
                    break;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error in Local IPC Server loop");
                    await Task.Delay(1000, cancellationToken); // Wait before retrying
                }
            }
        }

        /// <summary>
        /// Handle individual client connection
        /// </summary>
        private async Task HandleClientConnectionAsync(CancellationToken cancellationToken)
        {
            using var pipeServer = new NamedPipeServerStream(
                _config.PipeName,
                PipeDirection.InOut,
                1,
                PipeTransmissionMode.Byte,
                PipeOptions.Asynchronous
            );

            _logger.LogDebug("Waiting for client connection...");
            await pipeServer.WaitForConnectionAsync(cancellationToken);
            
            _logger.LogInformation("Client connected to Local IPC Server");
            
            try
            {
                await ProcessClientMessagesAsync(pipeServer, cancellationToken);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing client messages");
            }
            finally
            {
                if (pipeServer.IsConnected)
                {
                    pipeServer.Disconnect();
                }
                _logger.LogInformation("Client disconnected from Local IPC Server");
            }
        }

        /// <summary>
        /// Process messages from connected client
        /// </summary>
        private async Task ProcessClientMessagesAsync(
            NamedPipeServerStream pipeServer, 
            CancellationToken cancellationToken)
        {
            while (pipeServer.IsConnected && !cancellationToken.IsCancellationRequested)
            {
                try
                {
                    // Read message length
                    var lengthBytes = new byte[4];
                    var bytesRead = await pipeServer.ReadAsync(lengthBytes, 0, 4, cancellationToken);
                    
                    if (bytesRead == 0)
                    {
                        _logger.LogDebug("Client disconnected (no data)");
                        break;
                    }
                    
                    var messageLength = BitConverter.ToInt32(lengthBytes, 0);
                    
                    // Read message content
                    var messageBytes = new byte[messageLength];
                    var totalBytesRead = 0;
                    
                    while (totalBytesRead < messageLength)
                    {
                        var readBytes = await pipeServer.ReadAsync(
                            messageBytes, 
                            totalBytesRead, 
                            messageLength - totalBytesRead, 
                            cancellationToken
                        );
                        
                        if (readBytes == 0)
                        {
                            _logger.LogDebug("Client disconnected during message read");
                            break;
                        }
                        
                        totalBytesRead += readBytes;
                    }
                    
                    if (totalBytesRead < messageLength)
                    {
                        break; // Client disconnected
                    }
                    
                    // Deserialize and process message
                    var jsonMessage = Encoding.UTF8.GetString(messageBytes);
                    await ProcessMessageAsync(pipeServer, jsonMessage, cancellationToken);
                }
                catch (OperationCanceledException)
                {
                    break;
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error reading message from client");
                    break;
                }
            }
        }

        /// <summary>
        /// Process individual message and send response
        /// </summary>
        private async Task ProcessMessageAsync(
            NamedPipeServerStream pipeServer, 
            string jsonMessage, 
            CancellationToken cancellationToken)
        {
            try
            {
                var message = JsonSerializer.Deserialize<IPCMessage<object>>(jsonMessage, _jsonOptions);
                _logger.LogInformation("Received message: {MessageType}", message.MessageType);
                
                // Route message to appropriate handler
                var response = await _messageHandler.HandleMessageAsync(message, cancellationToken);
                
                // Send response back to client
                var responseJson = JsonSerializer.Serialize(response, _jsonOptions);
                var responseBytes = Encoding.UTF8.GetBytes(responseJson);
                
                // Send response length first
                var lengthBytes = BitConverter.GetBytes(responseBytes.Length);
                await pipeServer.WriteAsync(lengthBytes, 0, lengthBytes.Length, cancellationToken);
                
                // Send response content
                await pipeServer.WriteAsync(responseBytes, 0, responseBytes.Length, cancellationToken);
                await pipeServer.FlushAsync(cancellationToken);
                
                _logger.LogDebug("Response sent for message: {MessageType}", message.MessageType);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing message");
                
                // Send error response
                var errorResponse = new IPCResponse<object>
                {
                    Success = false,
                    Error = ex.Message,
                    Timestamp = DateTime.UtcNow
                };
                
                var errorJson = JsonSerializer.Serialize(errorResponse, _jsonOptions);
                var errorBytes = Encoding.UTF8.GetBytes(errorJson);
                
                var lengthBytes = BitConverter.GetBytes(errorBytes.Length);
                await pipeServer.WriteAsync(lengthBytes, 0, lengthBytes.Length, cancellationToken);
                await pipeServer.WriteAsync(errorBytes, 0, errorBytes.Length, cancellationToken);
                await pipeServer.FlushAsync(cancellationToken);
            }
        }

        #endregion

        #region Message Sending

        /// <summary>
        /// Send progress update to Desktop app
        /// </summary>
        public async Task SendProgressUpdateAsync(
            ProgressUpdate progressUpdate,
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Sending progress update: {Progress}%", progressUpdate.ProgressPercentage);
            
            try
            {
                using var pipeClient = new NamedPipeClientStream(
                    ".",
                    _config.PipeName,
                    PipeDirection.Out,
                    PipeOptions.Asynchronous
                );

                await pipeClient.ConnectAsync(_config.PipeTimeoutMs, cancellationToken);
                
                var message = new IPCMessage<ProgressUpdate>
                {
                    MessageType = "progress_update",
                    CorrelationId = progressUpdate.CorrelationId,
                    Data = progressUpdate,
                    Timestamp = DateTime.UtcNow
                };
                
                var jsonMessage = JsonSerializer.Serialize(message, _jsonOptions);
                var messageBytes = Encoding.UTF8.GetBytes(jsonMessage);
                
                // Send message length first
                var lengthBytes = BitConverter.GetBytes(messageBytes.Length);
                await pipeClient.WriteAsync(lengthBytes, 0, lengthBytes.Length, cancellationToken);
                
                // Send message content
                await pipeClient.WriteAsync(messageBytes, 0, messageBytes.Length, cancellationToken);
                await pipeClient.FlushAsync(cancellationToken);
                
                _logger.LogDebug("Progress update sent successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to send progress update");
            }
        }

        /// <summary>
        /// Send completion notification to Desktop app
        /// </summary>
        public async Task SendCompletionNotificationAsync(
            CompletionNotification notification,
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Sending completion notification: {Status}", notification.Status);
            
            try
            {
                using var pipeClient = new NamedPipeClientStream(
                    ".",
                    _config.PipeName,
                    PipeDirection.Out,
                    PipeOptions.Asynchronous
                );

                await pipeClient.ConnectAsync(_config.PipeTimeoutMs, cancellationToken);
                
                var message = new IPCMessage<CompletionNotification>
                {
                    MessageType = "completion_notification",
                    CorrelationId = notification.CorrelationId,
                    Data = notification,
                    Timestamp = DateTime.UtcNow
                };
                
                var jsonMessage = JsonSerializer.Serialize(message, _jsonOptions);
                var messageBytes = Encoding.UTF8.GetBytes(jsonMessage);
                
                // Send message length first
                var lengthBytes = BitConverter.GetBytes(messageBytes.Length);
                await pipeClient.WriteAsync(lengthBytes, 0, lengthBytes.Length, cancellationToken);
                
                // Send message content
                await pipeClient.WriteAsync(messageBytes, 0, messageBytes.Length, cancellationToken);
                await pipeClient.FlushAsync(cancellationToken);
                
                _logger.LogDebug("Completion notification sent successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to send completion notification");
            }
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
                _logger.LogInformation("Disposing Local IPC Server");
                
                _cancellationTokenSource?.Cancel();
                _serverTask?.Wait(5000); // Wait up to 5 seconds for graceful shutdown
                
                _cancellationTokenSource?.Dispose();
                _disposed = true;
            }
        }

        #endregion
    }

    /// <summary>
    /// Interface for Local IPC server
    /// </summary>
    public interface ILocalIPCServer : IDisposable
    {
        Task StartAsync(CancellationToken cancellationToken = default);
        Task StopAsync();
        Task SendProgressUpdateAsync(ProgressUpdate progressUpdate, CancellationToken cancellationToken = default);
        Task SendCompletionNotificationAsync(CompletionNotification notification, CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Interface for message handling
    /// </summary>
    public interface IMessageHandler
    {
        Task<IPCResponse<object>> HandleMessageAsync(IPCMessage<object> message, CancellationToken cancellationToken = default);
    }

    /// <summary>
    /// Progress update message
    /// </summary>
    public class ProgressUpdate
    {
        public string CorrelationId { get; set; }
        public string Stage { get; set; }
        public int ProgressPercentage { get; set; }
        public string Message { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Completion notification message
    /// </summary>
    public class CompletionNotification
    {
        public string CorrelationId { get; set; }
        public string Status { get; set; } // "success", "error", "cancelled"
        public string Message { get; set; }
        public object Result { get; set; }
        public DateTime Timestamp { get; set; }
    }
}
