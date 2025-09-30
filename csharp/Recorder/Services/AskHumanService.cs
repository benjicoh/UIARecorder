using Recorder.Dialogs;
using System.Windows;

namespace Recorder.Services
{
    public class AskHumanService : IAskHumanService
    {
        public string Ask(string prompt)
        {
            string response = "LLM No answer provided";
            Application.Current.Dispatcher.Invoke(() =>
            {
                var dialog = new AskHumanDialog(prompt)
                {
                    Owner = Application.Current.MainWindow
                };

                if (dialog.ShowDialog() == true)
                {
                    response = dialog.ResponseText;
                }
            });
            return response;
        }
    }
}