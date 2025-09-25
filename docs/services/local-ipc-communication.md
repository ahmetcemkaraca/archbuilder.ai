# Local IPC Communication Documentation

Bu dokümantasyon ArchBuilder.AI'nin Desktop uygulaması ve Revit plugin'i arasındaki Local IPC (Inter-Process Communication) sistemini detaylandırır.

## Genel Bakış

Local IPC sistemi, Desktop uygulaması ile Revit plugin'i arasında güvenli ve verimli iletişim sağlar. İki ana protokol desteklenir:

1. **Named Pipes** - Revit plugin ile Desktop app arasındaki gerçek zamanlı iletişim
2. **HTTP** - Desktop app ile local cloud server arasındaki REST API iletişimi

## Mimari

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Desktop App   │    │  Local Cloud     │    │   Revit Plugin  │
│                 │    │     Server       │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │IPC Client   │ │◄──►│ │ HTTP Server  │ │    │ │IPC Server   │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ └─────────────┘ │
│                 │    │                  │    │                 │
│ ┌─────────────┐ │    │ ┌──────────────┐ │    │ ┌─────────────┐ │
│ │HTTP Client  │ │◄──►│ │ AI Services  │ │    │ │Message      │ │
│ └─────────────┘ │    │ └──────────────┘ │    │ │Handler      │ │
│                 │    │                  │    │ └─────────────┘ │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                    ┌─────────────┴─────────────┐
                    │     Named Pipes           │
                    │   (Real-time IPC)         │
                    └───────────────────────────┘
```

## Named Pipes Communication

### Desktop App → Revit Plugin

#### Layout Generation Request
```csharp
var request = new LayoutGenerationRequest
{
    CorrelationId = "layout_123",
    UserPrompt = "3 bedroom apartment with modern kitchen",
    TotalAreaM2 = 120.0,
    BuildingType = "apartment",
    Language = "tr",
    Requirements = new List<string> { "Open kitchen", "Master bedroom with ensuite" },
    Constraints = new List<string> { "North-facing entrance", "Max 3m ceiling height" }
};

var response = await ipcClient.SendLayoutGenerationRequestAsync(request);
```

#### Validation Request
```csharp
var request = new ValidationRequest
{
    CorrelationId = "validation_123",
    Payload = layoutData,
    BuildingType = "apartment",
    ValidationType = "both" // "geometric", "code", "both"
};

var response = await ipcClient.SendValidationRequestAsync(request);
```

### Revit Plugin → Desktop App

#### Progress Updates
```csharp
var progressUpdate = new ProgressUpdate
{
    CorrelationId = "layout_123",
    Stage = "wall_creation",
    ProgressPercentage = 45,
    Message = "Creating interior walls...",
    Timestamp = DateTime.UtcNow
};

await ipcServer.SendProgressUpdateAsync(progressUpdate);
```

#### Completion Notifications
```csharp
var notification = new CompletionNotification
{
    CorrelationId = "layout_123",
    Status = "success",
    Message = "Layout generation completed successfully",
    Result = layoutResult,
    Timestamp = DateTime.UtcNow
};

await ipcServer.SendCompletionNotificationAsync(notification);
```

## HTTP Communication

### Desktop App → Local Cloud Server

#### AI Command Request
```csharp
var request = new AICommandRequest
{
    CorrelationId = "ai_cmd_123",
    Command = "generate_layout",
    Input = new { 
        user_prompt = "3 bedroom apartment",
        total_area = 120.0,
        building_type = "apartment"
    },
    UserId = "user_123",
    ProjectId = "project_123"
};

var response = await ipcClient.SendAICommandAsync(request);
```

#### Project Analysis Request
```csharp
var request = new ProjectAnalysisRequest
{
    CorrelationId = "analysis_123",
    ProjectId = "project_123",
    AnalysisType = "both",
    Options = new { 
        include_geometry = true,
        include_code_compliance = true
    }
};

var response = await ipcClient.SendProjectAnalysisAsync(request);
```

## Message Contracts

### Base Message Structure
```csharp
public class IPCMessage<T>
{
    public string MessageType { get; set; }
    public string CorrelationId { get; set; }
    public T Data { get; set; }
    public DateTime Timestamp { get; set; }
}
```

### Response Structure
```csharp
public class IPCResponse<T>
{
    public bool Success { get; set; }
    public string MessageType { get; set; }
    public string CorrelationId { get; set; }
    public T Data { get; set; }
    public string Error { get; set; }
    public DateTime Timestamp { get; set; }
}
```

## Configuration

### Local IPC Configuration
```csharp
public class LocalIPCConfiguration
{
    public string PipeName { get; set; } = "ArchBuilderIPC";
    public int PipeTimeoutMs { get; set; } = 5000;
    public string LocalServerUrl { get; set; } = "http://localhost:8000";
    public int HttpTimeoutMs { get; set; } = 30000;
    public int RetryAttempts { get; set; } = 3;
    public int RetryDelayMs { get; set; } = 1000;
}
```

### Dependency Injection Setup
```csharp
// Desktop App
services.AddSingleton<LocalIPCConfiguration>();
services.AddSingleton<ILocalIPCClient, LocalIPCClient>();

// Revit Plugin
services.AddSingleton<LocalIPCConfiguration>();
services.AddSingleton<ILocalIPCServer, LocalIPCServer>();
services.AddSingleton<IMessageHandler, RevitMessageHandler>();
```

## Error Handling

### Named Pipes Errors
```csharp
try
{
    var response = await ipcClient.SendNamedPipeMessageAsync(message);
    if (!response.Success)
    {
        _logger.LogError("IPC communication failed: {Error}", response.Error);
        // Handle error
    }
}
catch (TimeoutException ex)
{
    _logger.LogError(ex, "IPC communication timeout");
    // Handle timeout
}
catch (Exception ex)
{
    _logger.LogError(ex, "IPC communication error");
    // Handle general error
}
```

### HTTP Errors
```csharp
try
{
    var response = await ipcClient.SendHttpRequestAsync<object>(endpoint, data, correlationId);
    if (!response.Success)
    {
        _logger.LogError("HTTP communication failed: {Error}", response.Error);
        // Handle error
    }
}
catch (HttpRequestException ex)
{
    _logger.LogError(ex, "HTTP request failed");
    // Handle HTTP error
}
```

## Health Checks

### Check Local Server Availability
```csharp
var isServerAvailable = await ipcClient.IsLocalServerAvailableAsync();
if (!isServerAvailable)
{
    _logger.LogWarning("Local cloud server is not available");
    // Handle server unavailable
}
```

### Check Revit Plugin Availability
```csharp
var isPluginAvailable = await ipcClient.IsRevitPluginAvailableAsync();
if (!isPluginAvailable)
{
    _logger.LogWarning("Revit plugin is not available");
    // Handle plugin unavailable
}
```

## Performance Considerations

### Connection Pooling
```csharp
// Named Pipes connections are created per request
// No persistent connections to avoid resource leaks
using var pipeClient = new NamedPipeClientStream(...);
```

### Message Size Limits
```csharp
// Named Pipes have practical size limits
// Large messages should be chunked or use file transfer
const int MAX_MESSAGE_SIZE = 1024 * 1024; // 1MB
```

### Timeout Configuration
```csharp
// Configure appropriate timeouts based on operation type
var config = new LocalIPCConfiguration
{
    PipeTimeoutMs = 5000,      // Quick operations
    HttpTimeoutMs = 30000,     // AI operations may take longer
    RetryAttempts = 3,         // Retry failed operations
    RetryDelayMs = 1000        // Exponential backoff
};
```

## Security

### Message Validation
```csharp
public class MessageValidator
{
    public bool ValidateMessage<T>(IPCMessage<T> message)
    {
        if (string.IsNullOrEmpty(message.CorrelationId))
            return false;
            
        if (string.IsNullOrEmpty(message.MessageType))
            return false;
            
        if (message.Timestamp > DateTime.UtcNow.AddMinutes(5))
            return false; // Reject old messages
            
        return true;
    }
}
```

### Correlation ID Tracking
```csharp
// All messages must include correlation ID for tracking
var correlationId = Guid.NewGuid().ToString();
var message = new IPCMessage<T>
{
    CorrelationId = correlationId,
    // ... other properties
};
```

## Testing

### Unit Tests
```csharp
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
}
```

### Integration Tests
```csharp
[Fact]
public async Task NamedPipeCommunication_WithServer_WorksCorrectly()
{
    // Start test server
    using var testServer = new NamedPipeServerStream("TestPipe");
    
    // Test communication
    var result = await _client.SendNamedPipeMessageAsync(message);
    
    // Verify results
    Assert.True(result.Success);
}
```

## Monitoring

### Logging
```csharp
_logger.LogInformation("Sending IPC message: {MessageType}", message.MessageType);
_logger.LogError(ex, "IPC communication failed: {CorrelationId}", message.CorrelationId);
```

### Metrics
```csharp
// Track IPC communication metrics
_metrics.IncrementCounter("ipc_messages_sent", new { message_type = message.MessageType });
_metrics.RecordHistogram("ipc_message_duration", duration);
```

## Troubleshooting

### Common Issues

1. **Named Pipes Connection Failed**
   - Check if Revit plugin is loaded
   - Verify pipe name configuration
   - Check Windows Named Pipes permissions

2. **HTTP Communication Failed**
   - Check if local cloud server is running
   - Verify server URL configuration
   - Check firewall settings

3. **Message Serialization Errors**
   - Verify JSON serialization settings
   - Check message size limits
   - Validate message structure

### Debug Logging
```csharp
// Enable debug logging for IPC communication
services.AddLogging(builder =>
{
    builder.AddConsole();
    builder.SetMinimumLevel(LogLevel.Debug);
});
```

## Best Practices

1. **Always use correlation IDs** for message tracking
2. **Handle timeouts gracefully** with appropriate retry logic
3. **Validate messages** before processing
4. **Use appropriate timeouts** based on operation complexity
5. **Log all IPC communication** for debugging
6. **Dispose resources properly** to avoid memory leaks
7. **Test both success and failure scenarios**

## Changelog

### v1.0.0 (2025-01-10)
- İlk Local IPC implementasyonu
- Named Pipes ve HTTP communication
- Temel message contracts
- Error handling ve logging

### v1.1.0 (2025-01-15)
- Performance optimizasyonları
- Connection pooling
- Advanced error handling
- Health check endpoints

### v1.2.0 (2025-01-20)
- Security improvements
- Message validation
- Enhanced monitoring
- Comprehensive testing
