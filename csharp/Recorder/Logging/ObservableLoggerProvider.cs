using Microsoft.Extensions.Logging;
using Recorder.Models;
using System;
using System.Collections.Concurrent;

namespace Recorder.Logging
{
    public class ObservableLoggerProvider : ILoggerProvider
    {
        private readonly ConcurrentDictionary<string, ObservableLogger> _loggers = new ConcurrentDictionary<string, ObservableLogger>();
        private readonly Action<LogEntry> _logAction;

        public ObservableLoggerProvider(Action<LogEntry> logAction)
        {
            _logAction = logAction;
        }

        public ILogger CreateLogger(string categoryName)
        {
            return _loggers.GetOrAdd(categoryName, name => new ObservableLogger(name, _logAction));
        }

        public void Dispose()
        {
            _loggers.Clear();
        }
    }
}