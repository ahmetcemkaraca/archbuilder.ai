using Autodesk.Revit.DB;
using System;
using System.Collections.Generic;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Interface for creating Revit elements
    /// </summary>
    public interface IElementCreationService
    {
        /// <summary>
        /// Create walls from wall definitions
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="wallDefinitions">Wall definitions to create</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Created wall elements</returns>
        List<Wall> CreateWalls(Document document, List<WallDefinition> wallDefinitions, string correlationId);

        /// <summary>
        /// Create doors from door definitions
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="doorDefinitions">Door definitions to create</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Created door elements</returns>
        List<FamilyInstance> CreateDoors(Document document, List<DoorDefinition> doorDefinitions, string correlationId);

        /// <summary>
        /// Create windows from window definitions
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="windowDefinitions">Window definitions to create</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Created window elements</returns>
        List<FamilyInstance> CreateWindows(Document document, List<WindowDefinition> windowDefinitions, string correlationId);

        /// <summary>
        /// Create rooms from room definitions
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="roomDefinitions">Room definitions to create</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Created room elements</returns>
        List<Room> CreateRooms(Document document, List<RoomDefinition> roomDefinitions, string correlationId);

        /// <summary>
        /// Validate wall type exists in document
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="wallTypeName">Wall type name to validate</param>
        /// <returns>True if wall type exists</returns>
        bool ValidateWallType(Document document, string wallTypeName);

        /// <summary>
        /// Validate door family exists in document
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="familyName">Family name to validate</param>
        /// <param name="typeName">Type name to validate</param>
        /// <returns>True if family and type exist</returns>
        bool ValidateDoorFamily(Document document, string familyName, string typeName);

        /// <summary>
        /// Validate window family exists in document
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="familyName">Family name to validate</param>
        /// <param name="typeName">Type name to validate</param>
        /// <returns>True if family and type exist</returns>
        bool ValidateWindowFamily(Document document, string familyName, string typeName);

        /// <summary>
        /// Get or create level by name
        /// </summary>
        /// <param name="document">Revit document</param>
        /// <param name="levelName">Level name</param>
        /// <param name="elevation">Level elevation</param>
        /// <returns>Level element</returns>
        Level GetOrCreateLevel(Document document, string levelName, double elevation = 0.0);
    }

    /// <summary>
    /// Wall definition for creation
    /// </summary>
    public class WallDefinition
    {
        public string Id { get; set; }
        public XYZ StartPoint { get; set; }
        public XYZ EndPoint { get; set; }
        public double Height { get; set; }
        public string WallTypeName { get; set; }
        public string LevelName { get; set; }
        public bool IsExterior { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();
    }

    /// <summary>
    /// Door definition for creation
    /// </summary>
    public class DoorDefinition
    {
        public string Id { get; set; }
        public string HostWallId { get; set; }
        public double PositionRatio { get; set; }
        public string FamilyName { get; set; }
        public string TypeName { get; set; }
        public double Width { get; set; }
        public double Height { get; set; }
        public bool FlipHand { get; set; }
        public bool FlipFacing { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();
    }

    /// <summary>
    /// Window definition for creation
    /// </summary>
    public class WindowDefinition
    {
        public string Id { get; set; }
        public string HostWallId { get; set; }
        public double PositionRatio { get; set; }
        public string FamilyName { get; set; }
        public string TypeName { get; set; }
        public double Width { get; set; }
        public double Height { get; set; }
        public double SillHeight { get; set; }
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();
    }

    /// <summary>
    /// Room definition for creation
    /// </summary>
    public class RoomDefinition
    {
        public string Id { get; set; }
        public string Name { get; set; }
        public string Number { get; set; }
        public string LevelName { get; set; }
        public List<XYZ> BoundaryPoints { get; set; } = new List<XYZ>();
        public Dictionary<string, object> Parameters { get; set; } = new Dictionary<string, object>();
    }
}
