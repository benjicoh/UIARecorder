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
        private object _lock = new object();

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

            if (!IsEnabled(logLevel))
            {
                return;
            }

            var message = formatter(state, exception);
            string filePath = "unknown";
            int lineNumber = 0;
            string memberName = "unknown";

            var stackTrace = new System.Diagnostics.StackTrace(true);
            foreach (var frame in stackTrace.GetFrames())
            {
                var method = frame.GetMethod();
                var declaringType = method?.DeclaringType;
                if (declaringType == null)
                {
                    continue;
                }

                var ns = declaringType.Namespace;
                if (ns != null && (ns.StartsWith("Microsoft.Extensions.Logging") || ns == "Recorder.Logging"))
                {
                    continue;
                }

                // This should be the calling frame
                filePath = frame.GetFileName() ?? "unknown";
                lineNumber = frame.GetFileLineNumber();
                memberName = frame.GetMethod()?.Name ?? "unknown";
                break;
            }

            var logEntry = new LogEntry(logLevel, message, filePath, lineNumber, memberName);
            lock (_lock)
            {
                _logAction?.Invoke(logEntry);
            }
        }
    }
}