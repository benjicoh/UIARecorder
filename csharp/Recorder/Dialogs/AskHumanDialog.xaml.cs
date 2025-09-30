using System.Windows;

namespace Recorder.Dialogs
{
    public partial class AskHumanDialog : Window
    {
        public string ResponseText { get; private set; }

        public AskHumanDialog(string prompt)
        {
            InitializeComponent();
            PromptTextBlock.Text = prompt;
        }

        private void OkButton_Click(object sender, RoutedEventArgs e)
        {
            ResponseText = ResponseTextBox.Text;
            DialogResult = true;
        }

        private void CancelButton_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
        }
    }
}