using System.Windows;
using System.Windows.Controls;

namespace Recorder.Controls
{
    /// <summary>
    /// Interaction logic for AlertBar.xaml
    /// </summary>
    public partial class AlertBar : UserControl
    {
        public AlertBar()
        {
            InitializeComponent();
        }

        private void DismissButton_Click(object sender, RoutedEventArgs e)
        {
            this.Visibility = Visibility.Collapsed;
        }

        public void ShowAlert(string message)
        {
            MessageTextBlock.Text = message;
            this.Visibility = Visibility.Visible;
        }
    }
}