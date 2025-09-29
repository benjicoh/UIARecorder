using Microsoft.Extensions.Logging;
using Recorder.Models;
using System;
using System.Runtime.CompilerServices;

namespace Recorder.Logging
{
    public class ObservableLogger : ILogger
    {
        private readonly string _name;
        private readonly Action<LogEntry> _logAction;

        public ObservableLogger(string name, Action<LogEntry> logAction)
        {
            _name = name;
            _logAction = logAction;
        }

        public IDisposable BeginScope<TState>(TState state) => default;

        public bool IsEnabled(LogLevel logLevel) => true;

        public void Log<TState>(LogLevel logLevel, EventId eventId, TState state, Exception exception, Func<TState, Exception, string> formatter)
        {
            if (!IsEnabled(logLevel))
            {
                return;
            }

            var message = formatter(state, exception);
            var logEntry = new LogEntry(logLevel, message);

            _logAction?.Invoke(logEntry);
        }
    }
}