using Autodesk.Revit.Attributes;
using Autodesk.Revit.DB;
using Autodesk.Revit.UI;
using ArchBuilder.RevitAddin.Configuration;
using ArchBuilder.RevitAddin.Services;
using ArchBuilder.RevitAddin.Utilities;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace ArchBuilder.RevitAddin.Commands
{
    /// <summary>
    /// Main AI Layout Command for ArchBuilder.AI Revit Plugin
    /// Provides AI-powered architectural layout generation capabilities
    /// </summary>
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class AILayoutCommand : IExternalCommand
    {
        private ILogger<AILayoutCommand> _logger;
        private ICorrelationIdGenerator _correlationIdGenerator;
        private ILayoutService _layoutService;
        private IProjectAnalysisService _projectAnalysisService;
        private ILocalCommunicationService _communicationService;

        /// <summary>
        /// Execute the AI Layout command
        /// </summary>
        /// <param name="commandData">Revit command data</param>
        /// <param name="message">Return message</param>
        /// <param name="elements">Selected elements</param>
        /// <returns>Command result</returns>
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                // Initialize configuration and services
                InitializeServices();

                var correlationId = _correlationIdGenerator.GenerateCorrelationId("RVT");
                _logger.LogInformation("Starting AI Layout command with correlation ID: {CorrelationId}", correlationId);

                var document = commandData.Application.ActiveUIDocument.Document;
                var uiDocument = commandData.Application.ActiveUIDocument;

                // Show main dialog
                var dialog = new UI.AILayoutDialog(document, uiDocument, correlationId);
                var dialogResult = dialog.ShowDialog();

                if (dialogResult == true)
                {
                    _logger.LogInformation("AI Layout command completed successfully");
                    return Result.Succeeded;
                }
                else
                {
                    _logger.LogInformation("AI Layout command cancelled by user");
                    return Result.Cancelled;
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "Error executing AI Layout command");
                message = $"AI Layout command failed: {ex.Message}";
                return Result.Failed;
            }
        }

        /// <summary>
        /// Initialize services and dependencies
        /// </summary>
        private void InitializeServices()
        {
            try
            {
                // Initialize configuration if not already done
                ConfigurationManager.Initialize();

                // Get services from dependency injection
                _logger = ConfigurationManager.GetService<ILogger<AILayoutCommand>>();
                _correlationIdGenerator = ConfigurationManager.GetService<ICorrelationIdGenerator>();
                _layoutService = ConfigurationManager.GetService<ILayoutService>();
                _projectAnalysisService = ConfigurationManager.GetService<IProjectAnalysisService>();
                _communicationService = ConfigurationManager.GetService<ILocalCommunicationService>();

                _logger.LogInformation("Services initialized successfully");
            }
            catch (Exception ex)
            {
                // Fallback logging if configuration fails
                Console.WriteLine($"Error initializing services: {ex.Message}");
                throw;
            }
        }
    }

    /// <summary>
    /// Project Analysis Command for analyzing existing Revit projects
    /// </summary>
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ProjectAnalysisCommand : IExternalCommand
    {
        private ILogger<ProjectAnalysisCommand> _logger;
        private ICorrelationIdGenerator _correlationIdGenerator;
        private IProjectAnalysisService _projectAnalysisService;
        private ILocalCommunicationService _communicationService;

        /// <summary>
        /// Execute the Project Analysis command
        /// </summary>
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                // Initialize services
                InitializeServices();

                var correlationId = _correlationIdGenerator.GenerateCorrelationId("RVT");
                _logger.LogInformation("Starting Project Analysis command with correlation ID: {CorrelationId}", correlationId);

                var document = commandData.Application.ActiveUIDocument.Document;

                // Perform project analysis
                var analysisResult = _projectAnalysisService.AnalyzeProject(document, correlationId);
                
                // Send analysis data to desktop app
                var sendResult = _communicationService.SendProjectAnalysisAsync(analysisResult, correlationId).Result;
                
                if (sendResult)
                {
                    _logger.LogInformation("Project analysis completed and sent to desktop app");
                    TaskDialog.Show("Project Analysis", 
                        $"Analysis completed successfully!\n\n" +
                        $"Elements: {analysisResult.ElementMetrics.TotalElements}\n" +
                        $"Walls: {analysisResult.ElementMetrics.WallCount}\n" +
                        $"Doors: {analysisResult.ElementMetrics.DoorCount}\n" +
                        $"Windows: {analysisResult.ElementMetrics.WindowCount}\n" +
                        $"Rooms: {analysisResult.ElementMetrics.RoomCount}\n\n" +
                        $"Clashes: {analysisResult.ClashData.TotalClashes}\n" +
                        $"Issues: {analysisResult.ComplianceIssues.TotalIssues}\n" +
                        $"Recommendations: {analysisResult.Recommendations.Count}");
                    
                    return Result.Succeeded;
                }
                else
                {
                    _logger.LogError("Failed to send project analysis to desktop app");
                    TaskDialog.Show("Project Analysis", "Analysis completed but failed to send to desktop app.");
                    return Result.Failed;
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "Error executing Project Analysis command");
                message = $"Project Analysis command failed: {ex.Message}";
                return Result.Failed;
            }
        }

        private void InitializeServices()
        {
            try
            {
                ConfigurationManager.Initialize();
                _logger = ConfigurationManager.GetService<ILogger<ProjectAnalysisCommand>>();
                _correlationIdGenerator = ConfigurationManager.GetService<ICorrelationIdGenerator>();
                _projectAnalysisService = ConfigurationManager.GetService<IProjectAnalysisService>();
                _communicationService = ConfigurationManager.GetService<ILocalCommunicationService>();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing services: {ex.Message}");
                throw;
            }
        }
    }

    /// <summary>
    /// Review Queue Command for managing AI-generated layouts that require human review
    /// </summary>
    [Transaction(TransactionMode.Manual)]
    [Regeneration(RegenerationOption.Manual)]
    public class ReviewQueueCommand : IExternalCommand
    {
        private ILogger<ReviewQueueCommand> _logger;
        private ICorrelationIdGenerator _correlationIdGenerator;
        private ILayoutService _layoutService;
        private ILocalCommunicationService _communicationService;

        /// <summary>
        /// Execute the Review Queue command
        /// </summary>
        public Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                // Initialize services
                InitializeServices();

                var correlationId = _correlationIdGenerator.GenerateCorrelationId("RVT");
                _logger.LogInformation("Starting Review Queue command with correlation ID: {CorrelationId}", correlationId);

                var document = commandData.Application.ActiveUIDocument.Document;

                // Show review queue dialog
                var dialog = new UI.ReviewQueueDialog(document, correlationId);
                var dialogResult = dialog.ShowDialog();

                if (dialogResult == true)
                {
                    _logger.LogInformation("Review Queue command completed successfully");
                    return Result.Succeeded;
                }
                else
                {
                    _logger.LogInformation("Review Queue command cancelled by user");
                    return Result.Cancelled;
                }
            }
            catch (Exception ex)
            {
                _logger?.LogError(ex, "Error executing Review Queue command");
                message = $"Review Queue command failed: {ex.Message}";
                return Result.Failed;
            }
        }

        private void InitializeServices()
        {
            try
            {
                ConfigurationManager.Initialize();
                _logger = ConfigurationManager.GetService<ILogger<ReviewQueueCommand>>();
                _correlationIdGenerator = ConfigurationManager.GetService<ICorrelationIdGenerator>();
                _layoutService = ConfigurationManager.GetService<ILayoutService>();
                _communicationService = ConfigurationManager.GetService<ILocalCommunicationService>();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error initializing services: {ex.Message}");
                throw;
            }
        }
    }
}
