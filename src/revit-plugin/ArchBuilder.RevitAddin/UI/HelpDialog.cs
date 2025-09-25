using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace ArchBuilder.RevitAddin.UI
{
    /// <summary>
    /// Help dialog for ArchBuilder.AI documentation
    /// </summary>
    public partial class HelpDialog : Window
    {
        public HelpDialog()
        {
            InitializeComponent();
            InitializeUI();
        }

        private void InitializeUI()
        {
            try
            {
                // Set window properties
                Title = "ArchBuilder.AI - Help & Documentation";
                Width = 700;
                Height = 500;
                WindowStartupLocation = WindowStartupLocation.CenterScreen;
                ResizeMode = ResizeMode.CanResize;

                // Create main layout
                CreateMainLayout();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error initializing help dialog: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void CreateMainLayout()
        {
            var mainGrid = new Grid();
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            mainGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // Create content area
            var contentArea = CreateContentArea();
            Grid.SetRow(contentArea, 0);
            mainGrid.Children.Add(contentArea);

            // Create button area
            var buttonArea = CreateButtonArea();
            Grid.SetRow(buttonArea, 1);
            mainGrid.Children.Add(buttonArea);

            Content = mainGrid;
        }

        private Grid CreateContentArea()
        {
            var contentGrid = new Grid();
            contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            contentGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            // Left panel - Navigation
            var navigationPanel = CreateNavigationPanel();
            Grid.SetColumn(navigationPanel, 0);
            contentGrid.Children.Add(navigationPanel);

            // Right panel - Content
            var contentPanel = CreateContentPanel();
            Grid.SetColumn(contentPanel, 1);
            contentGrid.Children.Add(contentPanel);

            return contentGrid;
        }

        private GroupBox CreateNavigationPanel()
        {
            var groupBox = new GroupBox
            {
                Header = "Topics",
                Margin = new Thickness(5)
            };

            var stackPanel = new StackPanel
            {
                Orientation = Orientation.Vertical,
                Margin = new Thickness(10)
            };

            // Navigation buttons
            var buttons = new[]
            {
                new { Title = "Getting Started", Content = "Introduction to ArchBuilder.AI" },
                new { Title = "AI Layout Generation", Content = "How to use AI layout generation" },
                new { Title = "Project Analysis", Content = "Analyzing existing projects" },
                new { Title = "Review Queue", Content = "Managing AI-generated layouts" },
                new { Title = "Best Practices", Content = "Tips for better results" },
                new { Title = "Troubleshooting", Content = "Common issues and solutions" },
                new { Title = "API Reference", Content = "Technical documentation" }
            };

            foreach (var button in buttons)
            {
                var navButton = new Button
                {
                    Content = button.Title,
                    Height = 30,
                    Margin = new Thickness(2),
                    Background = Brushes.LightBlue,
                    Tag = button.Content
                };
                navButton.Click += NavigationButton_Click;
                stackPanel.Children.Add(navButton);
            }

            groupBox.Content = stackPanel;
            return groupBox;
        }

        private GroupBox CreateContentPanel()
        {
            var groupBox = new GroupBox
            {
                Header = "Documentation",
                Margin = new Thickness(5)
            };

            var stackPanel = new StackPanel
            {
                Orientation = Orientation.Vertical,
                Margin = new Thickness(10)
            };

            // Content text
            var contentTextBox = new TextBox
            {
                Name = "ContentTextBox",
                Height = 350,
                TextWrapping = System.Windows.TextWrapping.Wrap,
                IsReadOnly = true,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Text = GetWelcomeContent()
            };

            stackPanel.Children.Add(contentTextBox);

            groupBox.Content = stackPanel;
            return groupBox;
        }

        private Grid CreateButtonArea()
        {
            var buttonGrid = new Grid();
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            // Close button
            var closeButton = new Button
            {
                Content = "Close",
                Width = 80,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightGray
            };
            closeButton.Click += CloseButton_Click;
            Grid.SetColumn(closeButton, 1);
            buttonGrid.Children.Add(closeButton);

            // Open Documentation button
            var openDocButton = new Button
            {
                Content = "Open Full Documentation",
                Width = 180,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightGreen
            };
            openDocButton.Click += OpenDocButton_Click;
            Grid.SetColumn(openDocButton, 2);
            buttonGrid.Children.Add(openDocButton);

            return buttonGrid;
        }

        private void NavigationButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var button = sender as Button;
                var contentTextBox = FindName("ContentTextBox") as TextBox;

                if (button != null && contentTextBox != null)
                {
                    var topic = button.Content.ToString();
                    var content = GetContentForTopic(topic);
                    contentTextBox.Text = content;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error loading content: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            Close();
        }

        private void OpenDocButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // Open external documentation
                System.Diagnostics.Process.Start("https://docs.archbuilder.app");
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error opening documentation: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private string GetWelcomeContent()
        {
            return @"Welcome to ArchBuilder.AI!

ArchBuilder.AI is an AI-powered architectural design tool that integrates with Autodesk Revit to help architects create better designs faster.

Key Features:
• AI Layout Generation - Create architectural layouts using natural language
• Project Analysis - Analyze existing projects for improvements
• Review Queue - Manage AI-generated layouts with human oversight
• Building Code Compliance - Ensure designs meet regulatory requirements
• Multi-language Support - Works in multiple languages and regions

Getting Started:
1. Use the 'AI Layout' command to generate new layouts
2. Use 'Analyze Project' to review existing projects
3. Use 'Review Queue' to approve or modify AI suggestions

For detailed documentation, visit: https://docs.archbuilder.app

Need help? Contact support at: support@archbuilder.app";
        }

        private string GetContentForTopic(string topic)
        {
            switch (topic)
            {
                case "Getting Started":
                    return GetGettingStartedContent();
                case "AI Layout Generation":
                    return GetAILayoutContent();
                case "Project Analysis":
                    return GetProjectAnalysisContent();
                case "Review Queue":
                    return GetReviewQueueContent();
                case "Best Practices":
                    return GetBestPracticesContent();
                case "Troubleshooting":
                    return GetTroubleshootingContent();
                case "API Reference":
                    return GetAPIReferenceContent();
                default:
                    return GetWelcomeContent();
            }
        }

        private string GetGettingStartedContent()
        {
            return @"Getting Started with ArchBuilder.AI

1. Installation
   • Download and install the Revit plugin
   • Configure your API key in settings
   • Ensure internet connection for AI services

2. First Steps
   • Open a Revit project
   • Go to the ArchBuilder.AI ribbon tab
   • Click 'AI Layout' to start

3. Basic Workflow
   • Describe your requirements in natural language
   • Review AI-generated suggestions
   • Approve or modify as needed
   • Create the layout in Revit

4. Tips for Success
   • Be specific in your descriptions
   • Include area requirements
   • Mention style preferences
   • Consider building codes and regulations";
        }

        private string GetAILayoutContent()
        {
            return @"AI Layout Generation

How to Use:
1. Click 'AI Layout' in the ribbon
2. Describe your requirements in the text box
3. Specify building type and area
4. Click 'Generate Layout'
5. Review and approve the result

Best Practices:
• Use clear, descriptive language
• Include specific requirements
• Mention constraints and preferences
• Provide area and room information

Example Prompts:
• 'Create a 2-bedroom apartment with open plan living area'
• 'Design an office space with 10 workstations and 2 meeting rooms'
• 'Layout a retail store with display areas and storage'

The AI will generate:
• Wall layouts with proper dimensions
• Door and window placements
• Room definitions and areas
• Compliance with building codes";
        }

        private string GetProjectAnalysisContent()
        {
            return @"Project Analysis

The Project Analysis feature helps you:
• Identify optimization opportunities
• Check building code compliance
• Find performance issues
• Get improvement recommendations

What it Analyzes:
• Element counts and types
• Geometric relationships
• Building code compliance
• Performance metrics
• Clash detection

How to Use:
1. Click 'Analyze Project' in the ribbon
2. Wait for analysis to complete
3. Review the results
4. Follow recommendations

Analysis Results Include:
• Element metrics and counts
• Compliance issues
• Performance recommendations
• Clash detection results
• Improvement suggestions";
        }

        private string GetReviewQueueContent()
        {
            return @"Review Queue

The Review Queue manages AI-generated layouts that require human approval.

Features:
• View all pending layouts
• Review validation results
• Approve or reject layouts
• Request modifications
• Add review notes

Workflow:
1. AI generates layout
2. Layout appears in review queue
3. Architect reviews and validates
4. Approve, reject, or request changes
5. Layout is created in Revit

Review Criteria:
• Geometric validity
• Building code compliance
• Accessibility requirements
• Design intent alignment
• Quality and accuracy";
        }

        private string GetBestPracticesContent()
        {
            return @"Best Practices

For Better Results:

1. Clear Descriptions
   • Be specific about requirements
   • Include dimensions and areas
   • Mention style preferences
   • Specify constraints

2. Building Codes
   • Mention applicable codes
   • Include accessibility requirements
   • Consider regional regulations
   • Specify occupancy types

3. Review Process
   • Always review AI suggestions
   • Check validation results
   • Verify compliance
   • Make necessary adjustments

4. Project Setup
   • Use proper units and scales
   • Set up levels correctly
   • Configure wall types
   • Prepare family libraries

5. Iterative Design
   • Start with basic layouts
   • Refine through iterations
   • Use feedback for improvements
   • Learn from corrections";
        }

        private string GetTroubleshootingContent()
        {
            return @"Troubleshooting

Common Issues:

1. AI Service Not Responding
   • Check internet connection
   • Verify API key configuration
   • Try again after a few minutes
   • Contact support if persistent

2. Layout Generation Fails
   • Check input requirements
   • Ensure valid building type
   • Verify area specifications
   • Try simpler descriptions

3. Validation Errors
   • Review error messages
   • Check geometric constraints
   • Verify building codes
   • Adjust parameters as needed

4. Performance Issues
   • Close unnecessary applications
   • Check system resources
   • Optimize Revit model
   • Use smaller test projects

5. Plugin Not Loading
   • Check Revit version compatibility
   • Verify plugin installation
   • Restart Revit application
   • Reinstall if necessary

Support:
• Email: support@archbuilder.app
• Documentation: https://docs.archbuilder.app
• Community: https://community.archbuilder.app";
        }

        private string GetAPIReferenceContent()
        {
            return @"API Reference

ArchBuilder.AI provides APIs for:
• Layout generation
• Project analysis
• Validation services
• Communication protocols

Key Endpoints:
• POST /v1/ai/commands - Generate layouts
• GET /v1/ai/commands/{id} - Get results
• POST /v1/projects/analyze - Analyze projects
• GET /v1/validation/{id} - Get validation results

Authentication:
• API Key required
• Include in X-API-Key header
• Correlation ID for tracking

Data Formats:
• JSON request/response
• Millimeters for dimensions
• UTF-8 encoding
• ISO 8601 timestamps

Error Handling:
• HTTP status codes
• Detailed error messages
• Retry mechanisms
• Fallback options

For complete API documentation:
https://docs.archbuilder.app/api";
        }
    }
}
