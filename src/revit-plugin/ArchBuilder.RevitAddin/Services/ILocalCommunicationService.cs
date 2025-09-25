using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Interface for local communication between Revit plugin and desktop app
    /// </summary>
    public interface ILocalCommunicationService
    {
        /// <summary>
        /// Initialize the communication service
        /// </summary>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>True if initialization successful</returns>
        Task<bool> InitializeAsync(string correlationId);

        /// <summary>
        /// Send message to desktop app
        /// </summary>
        /// <param name="message">Message to send</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>True if message sent successfully</returns>
        Task<bool> SendMessageAsync(CommunicationMessage message, string correlationId);

        /// <summary>
        /// Receive message from desktop app
        /// </summary>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Received message or null if timeout</returns>
        Task<CommunicationMessage> ReceiveMessageAsync(string correlationId);

        /// <summary>
        /// Send project analysis data to desktop app
        /// </summary>
        /// <param name="analysisData">Project analysis data</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>True if data sent successfully</returns>
        Task<bool> SendProjectAnalysisAsync(ProjectAnalysisResult analysisData, string correlationId);

        /// <summary>
        /// Send layout generation request to desktop app
        /// </summary>
        /// <param name="layoutRequest">Layout generation request</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>True if request sent successfully</returns>
        Task<bool> SendLayoutRequestAsync(LayoutGenerationRequest layoutRequest, string correlationId);

        /// <summary>
        /// Receive layout generation response from desktop app
        /// </summary>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Layout generation response or null if timeout</returns>
        Task<LayoutGenerationResponse> ReceiveLayoutResponseAsync(string correlationId);

        /// <summary>
        /// Check if desktop app is available
        /// </summary>
        /// <returns>True if desktop app is available</returns>
        Task<bool> IsDesktopAppAvailableAsync();

        /// <summary>
        /// Dispose the communication service
        /// </summary>
        void Dispose();
    }

    /// <summary>
    /// Communication message structure
    /// </summary>
    public class CommunicationMessage
    {
        public string Id { get; set; }
        public string Type { get; set; }
        public string CorrelationId { get; set; }
        public DateTime Timestamp { get; set; }
        public object Payload { get; set; }
        public Dictionary<string, object> Headers { get; set; } = new Dictionary<string, object>();
    }

    /// <summary>
    /// Layout generation request
    /// </summary>
    public class LayoutGenerationRequest
    {
        public string Id { get; set; }
        public string UserPrompt { get; set; }
        public double TotalAreaM2 { get; set; }
        public string BuildingType { get; set; }
        public List<string> RequiredRooms { get; set; } = new List<string>();
        public Dictionary<string, object> Constraints { get; set; } = new Dictionary<string, object>();
        public Dictionary<string, object> StylePreferences { get; set; } = new Dictionary<string, object>();
    }

    /// <summary>
    /// Layout generation response
    /// </summary>
    public class LayoutGenerationResponse
    {
        public string Id { get; set; }
        public string RequestId { get; set; }
        public bool Success { get; set; }
        public string ErrorMessage { get; set; }
        public LayoutData LayoutData { get; set; }
        public ValidationResult Validation { get; set; }
        public bool RequiresHumanReview { get; set; }
        public DateTime Timestamp { get; set; }
    }

    /// <summary>
    /// Layout data structure
    /// </summary>
    public class LayoutData
    {
        public List<WallDefinition> Walls { get; set; } = new List<WallDefinition>();
        public List<DoorDefinition> Doors { get; set; } = new List<DoorDefinition>();
        public List<WindowDefinition> Windows { get; set; } = new List<WindowDefinition>();
        public List<RoomDefinition> Rooms { get; set; } = new List<RoomDefinition>();
        public Dictionary<string, object> Metadata { get; set; } = new Dictionary<string, object>();
    }

    /// <summary>
    /// Communication message types
    /// </summary>
    public static class MessageTypes
    {
        public const string PROJECT_ANALYSIS = "project_analysis";
        public const string LAYOUT_REQUEST = "layout_request";
        public const string LAYOUT_RESPONSE = "layout_response";
        public const string VALIDATION_REQUEST = "validation_request";
        public const string VALIDATION_RESPONSE = "validation_response";
        public const string ERROR = "error";
        public const string HEARTBEAT = "heartbeat";
        public const string STATUS_UPDATE = "status_update";
    }
}
