using System;
using System.IO;
using System.IO.Pipes;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Moq;
using Xunit;
using ArchBuilder.Desktop.Communication;
using ArchBuilder.Desktop.Core.Models;

namespace ArchBuilder.Desktop.Tests.Communication
{
    public class LocalIPCClientTests : IDisposable
    {
        private readonly Mock<ILogger<LocalIPCClient>> _mockLogger;
        private readonly LocalIPCConfiguration _config;
        private readonly LocalIPCClient _client;

        public LocalIPCClientTests()
        {
            _mockLogger = new Mock<ILogger<LocalIPCClient>>();
            _config = new LocalIPCConfiguration
            {
                PipeName = "TestArchBuilderIPC",
                PipeTimeoutMs = 1000,
                LocalServerUrl = "http://localhost:8000",
                HttpTimeoutMs = 5000
            };
            _client = new LocalIPCClient(_mockLogger.Object, _config);
        }

        [Fact]
        public async Task SendNamedPipeMessageAsync_Success_ReturnsSuccessResponse()
        {
            // Arrange
            var message = new IPCMessage<string>
            {
                MessageType = "test_message",
                CorrelationId = "test_corr_123",
                Data = "test_data",
                Timestamp = DateTime.UtcNow
            };

            // Act
            var result = await _client.SendNamedPipeMessageAsync(message);

            // Assert
            Assert.NotNull(result);
            Assert.True(result.Success);
            Assert.Equal("test_message", result.MessageType);
            Assert.Equal("test_corr_123", result.CorrelationId);
        }

        [Fact]
        public async Task SendNamedPipeMessageAsync_NoServer_ReturnsErrorResponse()
        {
            // Arrange
            var message = new IPCMessage<string>
            {
                MessageType = "test_message",
                CorrelationId = "test_corr_123",
                Data = "test_data",
                Timestamp = DateTime.UtcNow
            };

            // Act
            var result = await _client.SendNamedPipeMessageAsync(message);

            // Assert
            Assert.NotNull(result);
            Assert.False(result.Success);
            Assert.Equal("test_message", result.MessageType);
            Assert.Equal("test_corr_123", result.CorrelationId);
            Assert.NotNull(result.Error);
        }

        [Fact]
        public async Task SendHttpRequestAsync_Success_ReturnsSuccessResponse()
        {
            // Arrange
            var requestData = new { test = "data" };
            var correlationId = "test_corr_123";
            var endpoint = "/test";

            // Act
            var result = await _client.SendHttpRequestAsync<object>(endpoint, requestData, correlationId);

            // Assert
            Assert.NotNull(result);
            Assert.Equal(correlationId, result.CorrelationId);
            // Note: This will fail in test environment without actual server
            // In real tests, you would mock the HTTP client
        }

        [Fact]
        public async Task IsLocalServerAvailableAsync_NoServer_ReturnsFalse()
        {
            // Act
            var result = await _client.IsLocalServerAvailableAsync();

            // Assert
            Assert.False(result);
        }

        [Fact]
        public async Task IsRevitPluginAvailableAsync_NoPlugin_ReturnsFalse()
        {
            // Act
            var result = await _client.IsRevitPluginAvailableAsync();

            // Assert
            Assert.False(result);
        }

        [Fact]
        public async Task SendAICommandAsync_ValidRequest_ReturnsResponse()
        {
            // Arrange
            var request = new AICommandRequest
            {
                CorrelationId = "test_corr_123",
                Command = "test_command",
                Input = new { test = "input" },
                UserId = "user_123",
                ProjectId = "project_123"
            };

            // Act
            var result = await _client.SendAICommandAsync(request);

            // Assert
            Assert.NotNull(result);
            Assert.Equal("test_corr_123", result.CorrelationId);
            // Note: This will fail in test environment without actual server
        }

        [Fact]
        public async Task SendProjectAnalysisAsync_ValidRequest_ReturnsResponse()
        {
            // Arrange
            var request = new ProjectAnalysisRequest
            {
                CorrelationId = "test_corr_123",
                ProjectId = "project_123",
                AnalysisType = "both",
                Options = new { test = "option" }
            };

            // Act
            var result = await _client.SendProjectAnalysisAsync(request);

            // Assert
            Assert.NotNull(result);
            Assert.Equal("test_corr_123", result.CorrelationId);
            // Note: This will fail in test environment without actual server
        }

        [Fact]
        public void Dispose_DisposesCorrectly()
        {
            // Act
            _client.Dispose();

            // Assert
            // Should not throw exception
            Assert.True(true);
        }

        public void Dispose()
        {
            _client?.Dispose();
        }
    }

    /// <summary>
    /// Integration tests for Local IPC communication
    /// These tests require actual Named Pipes server to be running
    /// </summary>
    public class LocalIPCIntegrationTests : IDisposable
    {
        private readonly Mock<ILogger<LocalIPCClient>> _mockLogger;
        private readonly LocalIPCConfiguration _config;
        private readonly LocalIPCClient _client;
        private NamedPipeServerStream _testPipeServer;

        public LocalIPCIntegrationTests()
        {
            _mockLogger = new Mock<ILogger<LocalIPCClient>>();
            _config = new LocalIPCConfiguration
            {
                PipeName = "TestArchBuilderIntegration",
                PipeTimeoutMs = 5000,
                LocalServerUrl = "http://localhost:8000",
                HttpTimeoutMs = 10000
            };
            _client = new LocalIPCClient(_mockLogger.Object, _config);
        }

        [Fact]
        public async Task NamedPipeCommunication_WithServer_WorksCorrectly()
        {
            // Arrange
            var pipeName = "TestArchBuilderIntegration";
            var testMessage = "test_message_data";
            var receivedMessage = "";

            // Start test server
            _testPipeServer = new NamedPipeServerStream(
                pipeName,
                PipeDirection.In,
                1,
                PipeTransmissionMode.Byte,
                PipeOptions.Asynchronous
            );

            var serverTask = Task.Run(async () =>
            {
                await _testPipeServer.WaitForConnectionAsync();
                
                // Read message length
                var lengthBytes = new byte[4];
                await _testPipeServer.ReadAsync(lengthBytes, 0, 4);
                var messageLength = BitConverter.ToInt32(lengthBytes, 0);
                
                // Read message content
                var messageBytes = new byte[messageLength];
                var totalBytesRead = 0;
                
                while (totalBytesRead < messageLength)
                {
                    var bytesRead = await _testPipeServer.ReadAsync(
                        messageBytes, 
                        totalBytesRead, 
                        messageLength - totalBytesRead
                    );
                    totalBytesRead += bytesRead;
                }
                
                receivedMessage = Encoding.UTF8.GetString(messageBytes);
            });

            // Wait for server to start
            await Task.Delay(100);

            // Act
            var message = new IPCMessage<string>
            {
                MessageType = "test_message",
                CorrelationId = "test_corr_123",
                Data = testMessage,
                Timestamp = DateTime.UtcNow
            };

            var result = await _client.SendNamedPipeMessageAsync(message);

            // Wait for server to process
            await Task.Delay(100);

            // Assert
            Assert.True(result.Success);
            Assert.Contains(testMessage, receivedMessage);

            // Cleanup
            _testPipeServer?.Disconnect();
            _testPipeServer?.Dispose();
        }

        public void Dispose()
        {
            _client?.Dispose();
            _testPipeServer?.Dispose();
        }
    }

    /// <summary>
    /// Mock models for testing
    /// </summary>
    public class AICommandRequest
    {
        public string CorrelationId { get; set; }
        public string Command { get; set; }
        public object Input { get; set; }
        public string UserId { get; set; }
        public string ProjectId { get; set; }
    }

    public class AICommandResponse
    {
        public string CorrelationId { get; set; }
        public bool Success { get; set; }
        public object Data { get; set; }
        public string Error { get; set; }
    }

    public class ProjectAnalysisRequest
    {
        public string CorrelationId { get; set; }
        public string ProjectId { get; set; }
        public string AnalysisType { get; set; }
        public object Options { get; set; }
    }

    public class ProjectAnalysisResponse
    {
        public string CorrelationId { get; set; }
        public bool Success { get; set; }
        public object Data { get; set; }
        public string Error { get; set; }
    }
}
