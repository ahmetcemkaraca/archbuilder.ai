using System.Windows;

namespace ArchBuilder.Desktop.Views.Dialogs
{
    /// <summary>
    /// CloudSyncPermissionDialog.xaml için interaction logic
    /// </summary>
    public partial class CloudSyncPermissionDialog : Window
    {
        public CloudSyncPermissionDialog()
        {
            InitializeComponent();
        }

        private void AcceptButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = true;
            Close();
        }

        private void RejectButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}