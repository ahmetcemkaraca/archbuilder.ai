using Autodesk.Revit.UI;
using System;
using System.Drawing;
using System.IO;
using System.Reflection;

namespace ArchBuilder.RevitAddin.UI
{
    /// <summary>
    /// Ribbon panel for ArchBuilder.AI commands
    /// </summary>
    public class AutoPlanRibbonPanel
    {
        private const string TAB_NAME = "ArchBuilder.AI";
        private const string PANEL_NAME = "AI Layout Generation";

        /// <summary>
        /// Create the ribbon panel with all commands
        /// </summary>
        /// <param name="application">Revit UI application</param>
        public static void CreateRibbonPanel(UIControlledApplication application)
        {
            try
            {
                // Create custom tab
                application.CreateRibbonTab(TAB_NAME);

                // Create ribbon panel
                var ribbonPanel = application.CreateRibbonPanel(TAB_NAME, PANEL_NAME);

                // Get assembly path for button images
                var assemblyPath = Assembly.GetExecutingAssembly().Location;
                var assemblyDir = Path.GetDirectoryName(assemblyPath);

                // Create AI Layout command button
                var aiLayoutButton = new PushButtonData(
                    "AILayoutCommand",
                    "AI Layout",
                    assemblyPath,
                    "ArchBuilder.RevitAddin.Commands.AILayoutCommand")
                {
                    LongDescription = "Generate architectural layouts using AI. Create walls, doors, windows, and rooms based on natural language prompts.",
                    ToolTip = "AI Layout Generation",
                    Image = LoadButtonImage("AI_Layout_32.png"),
                    LargeImage = LoadButtonImage("AI_Layout_32.png")
                };

                // Create Project Analysis command button
                var projectAnalysisButton = new PushButtonData(
                    "ProjectAnalysisCommand",
                    "Analyze Project",
                    assemblyPath,
                    "ArchBuilder.RevitAddin.Commands.ProjectAnalysisCommand")
                {
                    LongDescription = "Analyze existing Revit project for improvements, compliance issues, and optimization opportunities.",
                    ToolTip = "Project Analysis",
                    Image = LoadButtonImage("Project_Analysis_32.png"),
                    LargeImage = LoadButtonImage("Project_Analysis_32.png")
                };

                // Create Review Queue command button
                var reviewQueueButton = new PushButtonData(
                    "ReviewQueueCommand",
                    "Review Queue",
                    assemblyPath,
                    "ArchBuilder.RevitAddin.Commands.ReviewQueueCommand")
                {
                    LongDescription = "Review and approve AI-generated layouts that require human validation.",
                    ToolTip = "Review Queue",
                    Image = LoadButtonImage("Review_Queue_32.png"),
                    LargeImage = LoadButtonImage("Review_Queue_32.png")
                };

                // Add buttons to panel
                ribbonPanel.AddItem(aiLayoutButton);
                ribbonPanel.AddSeparator();
                ribbonPanel.AddItem(projectAnalysisButton);
                ribbonPanel.AddItem(reviewQueueButton);

                // Add help button
                var helpButton = new PushButtonData(
                    "ArchBuilderHelp",
                    "Help",
                    assemblyPath,
                    "ArchBuilder.RevitAddin.Commands.HelpCommand")
                {
                    LongDescription = "Get help and documentation for ArchBuilder.AI features.",
                    ToolTip = "Help & Documentation",
                    Image = LoadButtonImage("Help_32.png"),
                    LargeImage = LoadButtonImage("Help_32.png")
                };

                ribbonPanel.AddSeparator();
                ribbonPanel.AddItem(helpButton);
            }
            catch (Exception ex)
            {
                // Log error but don't crash the plugin
                System.Diagnostics.Debug.WriteLine($"Error creating ribbon panel: {ex.Message}");
            }
        }

        /// <summary>
        /// Load button image from resources
        /// </summary>
        /// <param name="imageName">Image file name</param>
        /// <returns>Button image or null if not found</returns>
        private static Image LoadButtonImage(string imageName)
        {
            try
            {
                // Try to load from embedded resources first
                var assembly = Assembly.GetExecutingAssembly();
                var resourceName = $"ArchBuilder.RevitAddin.Resources.{imageName}";
                
                using (var stream = assembly.GetManifestResourceStream(resourceName))
                {
                    if (stream != null)
                    {
                        return Image.FromStream(stream);
                    }
                }

                // Fallback to file system
                var assemblyPath = Assembly.GetExecutingAssembly().Location;
                var assemblyDir = Path.GetDirectoryName(assemblyPath);
                var imagePath = Path.Combine(assemblyDir, "Resources", imageName);
                
                if (File.Exists(imagePath))
                {
                    return Image.FromFile(imagePath);
                }

                // Return default icon if no image found
                return CreateDefaultIcon();
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Error loading button image {imageName}: {ex.Message}");
                return CreateDefaultIcon();
            }
        }

        /// <summary>
        /// Create a default icon if no image is found
        /// </summary>
        /// <returns>Default icon</returns>
        private static Image CreateDefaultIcon()
        {
            try
            {
                // Create a simple 32x32 icon with "AI" text
                var bitmap = new Bitmap(32, 32);
                using (var graphics = Graphics.FromImage(bitmap))
                {
                    graphics.Clear(Color.LightBlue);
                    graphics.DrawString("AI", new Font("Arial", 12, FontStyle.Bold), Brushes.DarkBlue, 8, 8);
                }
                return bitmap;
            }
            catch
            {
                return null;
            }
        }
    }

    /// <summary>
    /// Help command for showing documentation
    /// </summary>
    [Autodesk.Revit.Attributes.Transaction(Autodesk.Revit.Attributes.TransactionMode.Manual)]
    [Autodesk.Revit.Attributes.Regeneration(Autodesk.Revit.Attributes.RegenerationOption.Manual)]
    public class HelpCommand : IExternalCommand
    {
        public Autodesk.Revit.UI.Result Execute(ExternalCommandData commandData, ref string message, ElementSet elements)
        {
            try
            {
                // Show help dialog
                var helpDialog = new HelpDialog();
                helpDialog.ShowDialog();

                return Autodesk.Revit.UI.Result.Succeeded;
            }
            catch (Exception ex)
            {
                message = $"Help command failed: {ex.Message}";
                return Autodesk.Revit.UI.Result.Failed;
            }
        }
    }
}