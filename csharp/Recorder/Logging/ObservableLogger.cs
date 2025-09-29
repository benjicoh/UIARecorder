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
            // This is a hack to get the caller info. It's not ideal, but it works without changing all call sites.
            var stackTrace = new System.Diagnostics.StackTrace(true);
            var frame = stackTrace.GetFrame(4); // Adjust the frame number as needed
            var filePath = frame?.GetFileName() ?? "unknown";
            var lineNumber = frame?.GetFileLineNumber() ?? 0;
            var memberName = frame?.GetMethod()?.Name ?? "unknown";


            var logEntry = new LogEntry(logLevel, message, filePath, lineNumber, memberName);

            _logAction?.Invoke(logEntry);
        }
    }
}