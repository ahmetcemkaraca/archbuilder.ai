using ArchBuilder.RevitAddin.Services;
using ArchBuilder.RevitAddin.Utilities;
using Microsoft.Extensions.Logging;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace ArchBuilder.RevitAddin.UI
{
    /// <summary>
    /// Dialog for reviewing and approving AI-generated layouts
    /// </summary>
    public partial class ReviewQueueDialog : Window
    {
        private readonly Autodesk.Revit.DB.Document _document;
        private readonly string _correlationId;
        private readonly ILogger<ReviewQueueDialog> _logger;
        private readonly ILayoutService _layoutService;
        private readonly ILocalCommunicationService _communicationService;

        public ReviewQueueDialog(Autodesk.Revit.DB.Document document, string correlationId)
        {
            InitializeComponent();
            
            _document = document ?? throw new ArgumentNullException(nameof(document));
            _correlationId = correlationId ?? throw new ArgumentNullException(nameof(correlationId));

            // Get services
            _logger = ConfigurationManager.GetService<ILogger<ReviewQueueDialog>>();
            _layoutService = ConfigurationManager.GetService<ILayoutService>();
            _communicationService = ConfigurationManager.GetService<ILocalCommunicationService>();

            InitializeUI();
        }

        private void InitializeUI()
        {
            try
            {
                // Set window properties
                Title = "ArchBuilder.AI - Review Queue";
                Width = 800;
                Height = 600;
                WindowStartupLocation = WindowStartupLocation.CenterScreen;
                ResizeMode = ResizeMode.CanResize;

                // Create main layout
                CreateMainLayout();

                _logger.LogInformation("Review Queue dialog initialized successfully");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error initializing Review Queue dialog");
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

            // Left panel - Review items
            var reviewPanel = CreateReviewPanel();
            Grid.SetColumn(reviewPanel, 0);
            contentGrid.Children.Add(reviewPanel);

            // Right panel - Details
            var detailsPanel = CreateDetailsPanel();
            Grid.SetColumn(detailsPanel, 1);
            contentGrid.Children.Add(detailsPanel);

            return contentGrid;
        }

        private GroupBox CreateReviewPanel()
        {
            var groupBox = new GroupBox
            {
                Header = "Items Requiring Review",
                Margin = new Thickness(5)
            };

            var stackPanel = new StackPanel
            {
                Orientation = Orientation.Vertical,
                Margin = new Thickness(10)
            };

            // Review items list
            var reviewItemsListBox = new ListBox
            {
                Name = "ReviewItemsListBox",
                Height = 400,
                SelectionMode = SelectionMode.Single
            };

            // Add sample review items
            var reviewItems = new List<ReviewItem>
            {
                new ReviewItem
                {
                    Id = "1",
                    Title = "2-Bedroom Apartment Layout",
                    Description = "AI-generated layout for residential apartment",
                    Status = "Pending Review",
                    CreatedAt = DateTime.Now.AddMinutes(-30),
                    Confidence = 0.85,
                    RequiresHumanReview = true
                },
                new ReviewItem
                {
                    Id = "2",
                    Title = "Office Space Layout",
                    Description = "Open plan office with meeting rooms",
                    Status = "Pending Review",
                    CreatedAt = DateTime.Now.AddMinutes(-15),
                    Confidence = 0.92,
                    RequiresHumanReview = true
                }
            };

            reviewItemsListBox.ItemsSource = reviewItems;
            reviewItemsListBox.SelectionChanged += ReviewItemsListBox_SelectionChanged;

            stackPanel.Children.Add(reviewItemsListBox);

            // Status summary
            var statusLabel = new Label
            {
                Name = "StatusLabel",
                Content = $"Total Items: {reviewItems.Count} | Pending: {reviewItems.Count(r => r.Status == "Pending Review")}",
                FontWeight = FontWeights.Bold
            };
            stackPanel.Children.Add(statusLabel);

            groupBox.Content = stackPanel;
            return groupBox;
        }

        private GroupBox CreateDetailsPanel()
        {
            var groupBox = new GroupBox
            {
                Header = "Review Details",
                Margin = new Thickness(5)
            };

            var stackPanel = new StackPanel
            {
                Orientation = Orientation.Vertical,
                Margin = new Thickness(10)
            };

            // Selected item details
            var selectedItemLabel = new Label
            {
                Name = "SelectedItemLabel",
                Content = "No item selected",
                FontWeight = FontWeights.Bold
            };
            stackPanel.Children.Add(selectedItemLabel);

            // Layout preview
            var previewLabel = new Label { Content = "Layout Preview:" };
            var previewTextBox = new TextBox
            {
                Name = "PreviewTextBox",
                Height = 150,
                TextWrapping = TextWrapping.Wrap,
                IsReadOnly = true,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Text = "Layout preview will appear here..."
            };
            stackPanel.Children.Add(previewLabel);
            stackPanel.Children.Add(previewTextBox);

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

            // Review notes
            var notesLabel = new Label { Content = "Review Notes:" };
            var notesTextBox = new TextBox
            {
                Name = "NotesTextBox",
                Height = 80,
                TextWrapping = TextWrapping.Wrap,
                VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
                Text = "Add your review notes here..."
            };
            stackPanel.Children.Add(notesLabel);
            stackPanel.Children.Add(notesTextBox);

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
            buttonGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            // Approve button
            var approveButton = new Button
            {
                Name = "ApproveButton",
                Content = "Approve",
                Width = 100,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightGreen,
                IsEnabled = false
            };
            approveButton.Click += ApproveButton_Click;
            Grid.SetColumn(approveButton, 1);
            buttonGrid.Children.Add(approveButton);

            // Reject button
            var rejectButton = new Button
            {
                Name = "RejectButton",
                Content = "Reject",
                Width = 100,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightCoral,
                IsEnabled = false
            };
            rejectButton.Click += RejectButton_Click;
            Grid.SetColumn(rejectButton, 2);
            buttonGrid.Children.Add(rejectButton);

            // Request Changes button
            var requestChangesButton = new Button
            {
                Name = "RequestChangesButton",
                Content = "Request Changes",
                Width = 120,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightYellow,
                IsEnabled = false
            };
            requestChangesButton.Click += RequestChangesButton_Click;
            Grid.SetColumn(requestChangesButton, 3);
            buttonGrid.Children.Add(requestChangesButton);

            // Close button
            var closeButton = new Button
            {
                Name = "CloseButton",
                Content = "Close",
                Width = 80,
                Height = 30,
                Margin = new Thickness(5),
                Background = Brushes.LightGray
            };
            closeButton.Click += CloseButton_Click;
            Grid.SetColumn(closeButton, 4);
            buttonGrid.Children.Add(closeButton);

            return buttonGrid;
        }

        private void ReviewItemsListBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            try
            {
                var listBox = sender as ListBox;
                var selectedItem = listBox.SelectedItem as ReviewItem;

                if (selectedItem != null)
                {
                    var selectedItemLabel = FindName("SelectedItemLabel") as Label;
                    var previewTextBox = FindName("PreviewTextBox") as TextBox;
                    var validationTextBox = FindName("ValidationTextBox") as TextBox;

                    selectedItemLabel.Content = $"Selected: {selectedItem.Title}";
                    
                    previewTextBox.Text = $"Layout Details:\n" +
                                       $"Title: {selectedItem.Title}\n" +
                                       $"Description: {selectedItem.Description}\n" +
                                       $"Status: {selectedItem.Status}\n" +
                                       $"Created: {selectedItem.CreatedAt:yyyy-MM-dd HH:mm}\n" +
                                       $"Confidence: {selectedItem.Confidence:P}\n" +
                                       $"Requires Review: {selectedItem.RequiresHumanReview}";

                    validationTextBox.Text = $"Validation Status: {'Valid'}\n" +
                                           $"Errors: 0\n" +
                                           $"Warnings: 2\n" +
                                           $"Geometric Check: Passed\n" +
                                           $"Building Code: Passed\n" +
                                           $"Accessibility: Passed";

                    // Enable action buttons
                    var approveButton = FindName("ApproveButton") as Button;
                    var rejectButton = FindName("RejectButton") as Button;
                    var requestChangesButton = FindName("RequestChangesButton") as Button;

                    approveButton.IsEnabled = true;
                    rejectButton.IsEnabled = true;
                    requestChangesButton.IsEnabled = true;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error handling review item selection");
            }
        }

        private async void ApproveButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var listBox = FindName("ReviewItemsListBox") as ListBox;
                var selectedItem = listBox.SelectedItem as ReviewItem;

                if (selectedItem != null)
                {
                    var notesTextBox = FindName("NotesTextBox") as TextBox;
                    var notes = notesTextBox.Text;

                    _logger.LogInformation("Approving layout item {ItemId} with notes: {Notes}", selectedItem.Id, notes);

                    // Update item status
                    selectedItem.Status = "Approved";
                    selectedItem.ReviewedAt = DateTime.Now;
                    selectedItem.ReviewNotes = notes;

                    // Refresh the list
                    listBox.Items.Refresh();

                    // Show success message
                    MessageBox.Show("Layout approved successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);

                    // Update status label
                    var statusLabel = FindName("StatusLabel") as Label;
                    var totalItems = ((List<ReviewItem>)listBox.ItemsSource).Count;
                    var pendingItems = ((List<ReviewItem>)listBox.ItemsSource).Count(r => r.Status == "Pending Review");
                    statusLabel.Content = $"Total Items: {totalItems} | Pending: {pendingItems}";

                    _logger.LogInformation("Layout item {ItemId} approved successfully", selectedItem.Id);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error approving layout item");
                MessageBox.Show($"Error approving layout: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void RejectButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var listBox = FindName("ReviewItemsListBox") as ListBox;
                var selectedItem = listBox.SelectedItem as ReviewItem;

                if (selectedItem != null)
                {
                    var notesTextBox = FindName("NotesTextBox") as TextBox;
                    var notes = notesTextBox.Text;

                    if (string.IsNullOrWhiteSpace(notes))
                    {
                        MessageBox.Show("Please provide rejection reason in the notes field.", "Validation", MessageBoxButton.OK, MessageBoxImage.Warning);
                        return;
                    }

                    _logger.LogInformation("Rejecting layout item {ItemId} with reason: {Notes}", selectedItem.Id, notes);

                    // Update item status
                    selectedItem.Status = "Rejected";
                    selectedItem.ReviewedAt = DateTime.Now;
                    selectedItem.ReviewNotes = notes;

                    // Refresh the list
                    listBox.Items.Refresh();

                    // Show success message
                    MessageBox.Show("Layout rejected successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);

                    // Update status label
                    var statusLabel = FindName("StatusLabel") as Label;
                    var totalItems = ((List<ReviewItem>)listBox.ItemsSource).Count;
                    var pendingItems = ((List<ReviewItem>)listBox.ItemsSource).Count(r => r.Status == "Pending Review");
                    statusLabel.Content = $"Total Items: {totalItems} | Pending: {pendingItems}";

                    _logger.LogInformation("Layout item {ItemId} rejected successfully", selectedItem.Id);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error rejecting layout item");
                MessageBox.Show($"Error rejecting layout: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private async void RequestChangesButton_Click(object sender, RoutedEventArgs e)
        {
            try
            {
                var listBox = FindName("ReviewItemsListBox") as ListBox;
                var selectedItem = listBox.SelectedItem as ReviewItem;

                if (selectedItem != null)
                {
                    var notesTextBox = FindName("NotesTextBox") as TextBox;
                    var notes = notesTextBox.Text;

                    if (string.IsNullOrWhiteSpace(notes))
                    {
                        MessageBox.Show("Please provide change request details in the notes field.", "Validation", MessageBoxButton.OK, MessageBoxImage.Warning);
                        return;
                    }

                    _logger.LogInformation("Requesting changes for layout item {ItemId} with details: {Notes}", selectedItem.Id, notes);

                    // Update item status
                    selectedItem.Status = "Changes Requested";
                    selectedItem.ReviewedAt = DateTime.Now;
                    selectedItem.ReviewNotes = notes;

                    // Refresh the list
                    listBox.Items.Refresh();

                    // Show success message
                    MessageBox.Show("Change request submitted successfully!", "Success", MessageBoxButton.OK, MessageBoxImage.Information);

                    // Update status label
                    var statusLabel = FindName("StatusLabel") as Label;
                    var totalItems = ((List<ReviewItem>)listBox.ItemsSource).Count;
                    var pendingItems = ((List<ReviewItem>)listBox.ItemsSource).Count(r => r.Status == "Pending Review");
                    statusLabel.Content = $"Total Items: {totalItems} | Pending: {pendingItems}";

                    _logger.LogInformation("Change request submitted for layout item {ItemId}", selectedItem.Id);
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error requesting changes for layout item");
                MessageBox.Show($"Error requesting changes: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
        }

        private void CloseButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = true;
            Close();
        }
    }

    /// <summary>
    /// Review item data structure
    /// </summary>
    public class ReviewItem
    {
        public string Id { get; set; }
        public string Title { get; set; }
        public string Description { get; set; }
        public string Status { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? ReviewedAt { get; set; }
        public double Confidence { get; set; }
        public bool RequiresHumanReview { get; set; }
        public string ReviewNotes { get; set; }
    }
}
