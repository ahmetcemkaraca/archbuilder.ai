using ArchBuilder.RevitAddin.Services;
using ArchBuilder.RevitAddin.Utilities;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace ArchBuilder.RevitAddin.UI
{
    /// <summary>
    /// Main dialog for AI Layout generation
    /// </summary>
    public partial class AILayoutDialog : Window
    {
        private readonly Autodesk.Revit.DB.Document _document;
        private readonly Autodesk.Revit.UI.UIDocument _uiDocument;
        private readonly string _correlationId;
        private readonly ILogger<AILayoutDialog> _logger;
        private readonly ILayoutService _layoutService;
        private readonly ILocalCommunicationService _communicationService;
        private readonly ICorrelationIdGenerator _correlationIdGenerator;

        public AILayoutDialog(Autodesk.Revit.DB.Document document, Autodesk.Revit.UI.UIDocument uiDocument, string correlationId)
        {
            InitializeComponent();
            
            _document = document ?? throw new ArgumentNullException(nameof(document));
            _uiDocument = uiDocument ?? throw new ArgumentNullException(nameof(uiDocument));
            _correlationId = correlationId ?? throw new ArgumentNullException(nameof(correlationId));

            // Get services
            _logger = ConfigurationManager.GetService<ILogger<AILayoutDialog>>();
            _layoutService = ConfigurationManager.GetService<ILayoutService>();
            _communicationService = ConfigurationManager.GetService<ILocalCommunicationService>();
            _correlationIdGenerator = ConfigurationManager.GetService<ICorrelationIdGenerator>();

            InitializeUI();
        }

        private void InitializeUI()
        {
            try
            {
                // Set window properties
                Title = "ArchBuilder.AI - AI Layout Generation";
                Width = 600;
                Height = 500;
                WindowStartupLocation = WindowStartupLocation.CenterScreen;
                ResizeMode = ResizeMode.CanResize;

                // Create main layout
                CreateMainLayout();

                _logger.LogInformation("AI Layout dialog initialized successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error initializing AI Layout dialog");
                MessageBox.Show($"Error initializing dialog: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
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

            // Left panel - Input
            var inputPanel = CreateInputPanel();
            Grid.SetColumn(inputPanel, 0);
            contentGrid.Children.Add(inputPanel);

            // Right panel - Output/Preview
            var outputPanel = CreateOutputPanel();
            Grid.SetColumn(outputPanel, 1);
            contentGrid.Children.Add(outputPanel);

            return contentGrid;
        }

        private GroupBox CreateInputPanel()
        {
            var groupBox = new GroupBox
            {
                Header = "Layout Requirements",
                Margin = new Thickness(5)
            };

            var stackPanel = new StackPanel
            {
                Orientation = Orientation.Vertical,
                Margin = new Thickness(10)
            };

            // User prompt input
            var promptLabel = new Label { Content = "Describe your layout requirements:" };
            var promptTextBox = new TextBox
            {
                Name = "PromptTextBox",
                Height = 100,
                TextWrapping = TextWrapping.Wrap,
                AcceptsReturn = true,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Text = "Create a 2-bedroom apartment with living room, kitchen, and bathroom. Total area should be around 80 square meters."
            };
            stackPanel.Children.Add(promptLabel);
            stackPanel.Children.Add(promptTextBox);

            // Building type
            var buildingTypeLabel = new Label { Content = "Building Type:" };
            var buildingTypeComboBox = new ComboBox
            {
                Name = "BuildingTypeComboBox",
                ItemsSource = new[] { "Residential", "Office", "Retail", "Industrial" },
                SelectedIndex = 0
            };
            stackPanel.Children.Add(buildingTypeLabel);
            stackPanel.Children.Add(buildingTypeComboBox);

            // Total area
            var areaLabel = new Label { Content = "Total Area (m²):" };
            var areaTextBox = new TextBox
            {
                Name = "AreaTextBox",
                Text = "80"
            };
            stackPanel.Children.Add(areaLabel);
            stackPanel.Children.Add(areaTextBox);

            // Required rooms
            var roomsLabel = new Label { Content = "Required Rooms:" };
            var roomsTextBox = new TextBox
            {
                Name = "RoomsTextBox",
                Text = "Living Room, Kitchen, Bedroom 1, Bedroom 2, Bathroom",
                TextWrapping = TextWrapping.Wrap
            };
            stackPanel.Children.Add(roomsLabel);
            stackPanel.Children.Add(roomsTextBox);

            // Style preferences
            var styleLabel = new Label { Content = "Style Preferences:" };
            var styleTextBox = new TextBox
            {
                Name = "StyleTextBox",
                Text = "Modern, open plan living area",
                TextWrapping = TextWrapping.Wrap
            };
            stackPanel.Children.Add(styleLabel);
            stackPanel.Children.Add(styleTextBox);

            groupBox.Content = stackPanel;
            return groupBox;
        }

        private GroupBox CreateOutputPanel()
        {
            var groupBox = new GroupBox
            {
                Header = "AI Response & Preview",
                Margin = new Thickness(5)
            };

            var stackPanel = new StackPanel
            {
                Orientation = Orientation.Vertical,
                Margin = new Thickness(10)
            };

            // Status
            var statusLabel = new Label
            {
                Name = "StatusLabel",
                Content = "Ready to generate layout",
                Foreground = Brushes.Green
            };
            stackPanel.Children.Add(statusLabel);

            // Progress bar
            var progressBar = new ProgressBar
            {
                Name = "ProgressBar",
                Height = 20,
                IsIndeterminate = false,
                Visibility = Visibility.Collapsed
            };
            stackPanel.Children.Add(progressBar);

            // AI response text
            var responseLabel = new Label { Content = "AI Response:" };
            var responseTextBox = new TextBox
            {
                Name = "ResponseTextBox",
                Height = 200,
                TextWrapping = TextWrapping.Wrap,
                IsReadOnly = true,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Text = "AI response will appear here..."
            };
            stackPanel.Children.Add(responseLabel);
            stackPanel.Children.Add(responseTextBox);

            // Validation results
            var validationLabel = new Label { Content = "Validation Results:" };
            var validationTextBox = new TextBox
            {
                Name = "ValidationTextBox",
                Height = 100,
                TextWrapping = TextWrapping.Wrap,
                IsReadOnly = true,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Text = "Validation results will appear here..."
            };
            stackPanel.Children.Add(validationLabel);
            stackPanel.Children.Add(validationTextBox);

            groupBox.Content = stackPanel;
            return groupBox;
        }

        private Grid CreateButtonArea()
        {
            var buttonGrid = new Grid();
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            // Generate button
            var generateButton = new Button
            {
                Name = "GenerateButton",
                Content = "Generate Layout",
                Width = 120,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightBlue
            };
            generateButton.Click += GenerateButton_Click;
            Grid.SetColumn(generateButton, 1);
            buttonGrid.Children.Add(generateButton);

            // Review button
            var reviewButton = new Button
            {
                Name = "ReviewButton",
                Content = "Review & Approve",
                Width = 120,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightGreen,
                IsEnabled = false
            };
            reviewButton.Click += ReviewButton_Click;
            Grid.SetColumn(reviewButton, 2);
            buttonGrid.Children.Add(reviewButton);

            // Cancel button
            var cancelButton = new Button
            {
                Name = "CancelButton",
                Content = "Cancel",
                Width = 80,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightCoral
            };
            cancelButton.Click += CancelButton_Click;
            Grid.SetColumn(cancelButton, 3);
            buttonGrid.Children.Add(cancelButton);

            return buttonGrid;
        }

        private async void GenerateButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var generateButton = sender as Button;
                generateButton.IsEnabled = false;
                generateButton.Content = "Generating...";

                var progressBar = FindName("ProgressBar") as ProgressBar;
                var statusLabel = FindName("StatusLabel") as Label;
                var responseTextBox = FindName("ResponseTextBox") as TextBox;
                var validationTextBox = FindName("ValidationTextBox") as TextBox;

                progressBar.Visibility = Visibility.Visible;
                progressBar.IsIndeterminate = true;
                statusLabel.Content = "Generating layout with AI...";
                statusLabel.Foreground = Brushes.Orange;

                // Get input values
                var promptTextBox = FindName("PromptTextBox") as TextBox;
                var buildingTypeComboBox = FindName("BuildingTypeComboBox") as ComboBox;
                var areaTextBox = FindName("AreaTextBox") as TextBox;
                var roomsTextBox = FindName("RoomsTextBox") as TextBox;
                var styleTextBox = FindName("StyleTextBox") as TextBox;

                var layoutRequest = new LayoutGenerationRequest
                {
                    Id = Guid.NewGuid().ToString(),
                    UserPrompt = promptTextBox.Text,
                    BuildingType = buildingTypeComboBox.SelectedItem?.ToString() ?? "Residential",
                    TotalAreaM2 = double.TryParse(areaTextBox.Text, out double area) ? area : 80.0,
                    RequiredRooms = roomsTextBox.Text.Split(',').Select(r => r.Trim()).ToList(),
                    StylePreferences = new Dictionary<string, object>
                    {
                        ["style"] = styleTextBox.Text
                    }
                };

                // Send request to desktop app
                var sendResult = await _communicationService.SendLayoutRequestAsync(layoutRequest, _correlationId);
                
                if (sendResult)
                {
                    statusLabel.Content = "Waiting for AI response...";
                    
                    // Wait for response
                    var response = await _communicationService.ReceiveLayoutResponseAsync(_correlationId);
                    
                    if (response != null && response.Success)
                    {
                        responseTextBox.Text = $"Layout generated successfully!\n\n" +
                                             $"Walls: {response.LayoutData.Walls.Count}\n" +
                                             $"Doors: {response.LayoutData.Doors.Count}\n" +
                                             $"Windows: {response.LayoutData.Windows.Count}\n" +
                                             $"Rooms: {response.LayoutData.Rooms.Count}\n\n" +
                                             $"Requires Human Review: {response.RequiresHumanReview}";

                        if (response.Validation != null)
                        {
                            validationTextBox.Text = $"Validation Results:\n" +
                                                    $"Valid: {response.Validation.IsValid}\n" +
                                                    $"Errors: {response.Validation.Errors.Count}\n" +
                                                    $"Warnings: {response.Validation.Warnings.Count}";
                        }

                        statusLabel.Content = "Layout generated successfully!";
                        statusLabel.Foreground = Brushes.Green;

                        // Enable review button
                        var reviewButton = FindName("ReviewButton") as Button;
                        reviewButton.IsEnabled = true;
                    }
                    else
                    {
                        responseTextBox.Text = response?.ErrorMessage ?? "Failed to receive AI response";
                        statusLabel.Content = "AI generation failed";
                        statusLabel.Foreground = Brushes.Red;
                    }
                }
                else
                {
                    responseTextBox.Text = "Failed to send request to desktop app";
                    statusLabel.Content = "Communication failed";
                    statusLabel.Foreground = Brushes.Red;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during layout generation");
                MessageBox.Show($"Error generating layout: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                var generateButton = FindName("GenerateButton") as Button;
                generateButton.IsEnabled = true;
                generateButton.Content = "Generate Layout";

                var progressBar = FindName("ProgressBar") as ProgressBar;
                progressBar.Visibility = Visibility.Collapsed;
                progressBar.IsIndeterminate = false;
            }
        }

        private void ReviewButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                // Show review dialog
                var reviewDialog = new ReviewQueueDialog(_document, _correlationId);
                var result = reviewDialog.ShowDialog();

                if (result == true)
                {
                    var statusLabel = FindName("StatusLabel") as Label;
                    statusLabel.Content = "Layout approved and created!";
                    statusLabel.Foreground = Brushes.Green;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error during review process");
                MessageBox.Show($"Error during review: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void CancelButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
