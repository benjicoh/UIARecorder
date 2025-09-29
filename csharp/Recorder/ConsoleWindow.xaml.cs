using Recorder.Models;
using Recorder.Utils;
using Recorder.ViewModels;
using System.Collections.Specialized;
using System.Windows;
using System.Windows.Documents;
using System.Windows.Media;

namespace Recorder
{
    public partial class ConsoleWindow : Window
    {
        private readonly LogLevelToBrushConverter _logLevelToBrushConverter = new LogLevelToBrushConverter();

        public ConsoleWindow()
        {
            InitializeComponent();
            DataContextChanged += OnDataContextChanged;
            this.Closing += (s, e) =>
            {
                this.Hide();
                e.Cancel = true; // Cancel the close operation
            };
        }

        private void OnDataContextChanged(object sender, DependencyPropertyChangedEventArgs e)
        {
            if (e.OldValue is MainViewModel oldVm)
            {
                oldVm.LogMessages.CollectionChanged -= OnLogMessagesChanged;
            }

            if (e.NewValue is MainViewModel newVm)
            {
                // Populate existing logs
                LogRichTextBox.Document.Blocks.Clear();
                foreach (var logEntry in newVm.LogMessages)
                {
                    AppendLog(logEntry);
                }
                LogRichTextBox.ScrollToEnd();

                // Subscribe to new logs
                newVm.LogMessages.CollectionChanged += OnLogMessagesChanged;
            }
        }

        private void OnLogMessagesChanged(object sender, NotifyCollectionChangedEventArgs e)
        {
            if (e.Action == NotifyCollectionChangedAction.Add)
            {
                var scrollAtEnd = LogRichTextBox.VerticalOffset + LogRichTextBox.ViewportHeight >= LogRichTextBox.ExtentHeight - 5; // Small tolerance

                foreach (LogEntry logEntry in e.NewItems)
                {
                    Dispatcher.Invoke(() => AppendLog(logEntry));
                }

                if (scrollAtEnd)
                {
                    LogRichTextBox.ScrollToEnd();
                }
            }
        }

        private void AppendLog(LogEntry logEntry)
        {
            var brush = (Brush)_logLevelToBrushConverter.Convert(logEntry.Level, typeof(Brush), null, System.Globalization.CultureInfo.CurrentCulture);
            var paragraph = new Paragraph();
            paragraph.Inlines.Add(new Run(logEntry.ToString()) { Foreground = brush });
            LogRichTextBox.Document.Blocks.Add(paragraph);
        }
    }
}