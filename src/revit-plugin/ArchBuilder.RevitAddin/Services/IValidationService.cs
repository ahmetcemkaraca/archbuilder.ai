using Autodesk.Revit.DB;
using System;
using System.Collections.Generic;

namespace ArchBuilder.RevitAddin.Services
{
    /// <summary>
    /// Interface for validating Revit elements and operations
    /// </summary>
    public interface IValidationService
    {
        /// <summary>
        /// Validate a single element
        /// </summary>
        /// <param name="element">Element to validate</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Validation result</returns>
        ElementValidationResult ValidateElement(Element element, string correlationId);

        /// <summary>
        /// Validate geometric constraints
        /// </summary>
        /// <param name="walls">Walls to validate</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Geometric validation result</returns>
        GeometricValidationResult ValidateGeometry(IEnumerable<Wall> walls, string correlationId);

        /// <summary>
        /// Validate building code compliance
        /// </summary>
        /// <param name="elements">Elements to validate</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Building code validation result</returns>
        BuildingCodeValidationResult ValidateBuildingCode(IEnumerable<Element> elements, string correlationId);

        /// <summary>
        /// Validate accessibility requirements
        /// </summary>
        /// <param name="doors">Doors to validate</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Accessibility validation result</returns>
        AccessibilityValidationResult ValidateAccessibility(IEnumerable<FamilyInstance> doors, string correlationId);

        /// <summary>
        /// Validate room areas
        /// </summary>
        /// <param name="rooms">Rooms to validate</param>
        /// <param name="correlationId">Correlation ID for tracking</param>
        /// <returns>Room area validation result</returns>
        RoomAreaValidationResult ValidateRoomAreas(IEnumerable<Room> rooms, string correlationId);
    }

    /// <summary>
    /// Element validation result
    /// </summary>
    public class ElementValidationResult
    {
        public bool IsValid { get; set; }
        public List<string> Errors { get; set; } = new List<string>();
        public List<string> Warnings { get; set; } = new List<string>();
        public string ElementId { get; set; }
        public string ElementType { get; set; }
    }

    /// <summary>
    /// Geometric validation result
    /// </summary>
    public class GeometricValidationResult
    {
        public bool IsValid { get; set; }
        public List<string> Errors { get; set; } = new List<string>();
        public List<string> Warnings { get; set; } = new List<string>();
        public int WallCount { get; set; }
        public double TotalLength { get; set; }
        public List<GeometricIssue> Issues { get; set; } = new List<GeometricIssue>();
    }

    /// <summary>
    /// Building code validation result
    /// </summary>
    public class BuildingCodeValidationResult
    {
        public bool IsCompliant { get; set; }
        public List<string> Violations { get; set; } = new List<string>();
        public List<string> Warnings { get; set; } = new List<string>();
        public string BuildingCode { get; set; }
        public string Region { get; set; }
    }

    /// <summary>
    /// Accessibility validation result
    /// </summary>
    public class AccessibilityValidationResult
    {
        public bool IsCompliant { get; set; }
        public List<string> Violations { get; set; } = new List<string>();
        public List<string> Warnings { get; set; } = new List<string>();
        public string Standard { get; set; }
        public int NonCompliantDoors { get; set; }
    }

    /// <summary>
    /// Room area validation result
    /// </summary>
    public class RoomAreaValidationResult
    {
        public bool IsValid { get; set; }
        public List<string> Errors { get; set; } = new List<string>();
        public List<string> Warnings { get; set; } = new List<string>();
        public int RoomCount { get; set; }
        public double TotalArea { get; set; }
        public List<RoomAreaIssue> Issues { get; set; } = new List<RoomAreaIssue>();
    }

    /// <summary>
    /// Geometric issue details
    /// </summary>
    public class GeometricIssue
    {
        public string Type { get; set; }
        public string Description { get; set; }
        public string ElementId { get; set; }
        public string Severity { get; set; }
    }

    /// <summary>
    /// Room area issue details
    /// </summary>
    public class RoomAreaIssue
    {
        public string RoomId { get; set; }
        public string RoomName { get; set; }
        public double CurrentArea { get; set; }
        public double MinimumArea { get; set; }
        public string IssueType { get; set; }
    }
}
