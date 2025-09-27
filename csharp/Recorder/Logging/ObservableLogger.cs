using Microsoft.Extensions.Logging;
using System;
using System.Runtime.CompilerServices;

namespace Recorder.Logging
{
    public class ObservableLogger : ILogger
    {
        private readonly string _name;
        private readonly Action<string> _logAction;

        public ObservableLogger(string name, Action<string> logAction)
        {
            _name = name;
            _logAction = logAction;
        }

        public IDisposable BeginScope<TState>(TState state) => default;

        public bool IsEnabled(LogLevel logLevel) => true;

        public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception exception, Func<TState, Exception, string> formatter,
            [CallerFilePath] string filePath = "", [CallerLineNumber] int lineNumber = 0)
        {
            if (!IsEnabled(logLevel))
            {
                return;
            }

            var message = formatter(state, exception);
            var level = logLevel.ToString().ToUpper();
            var finalMessage = $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} - {System.IO.Path.GetFileName(filePath)}:{lineNumber} - {level} - {message}";

            _logAction?.Invoke(finalMessage);
        }
    }
}