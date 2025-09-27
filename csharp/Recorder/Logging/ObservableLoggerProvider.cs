using Microsoft.Extensions.Logging;
using System;
using System.Collections.Concurrent;

namespace Recorder.Logging
{
    public class ObservableLoggerProvider : ILoggerProvider
    {
        private readonly ConcurrentDictionary<string, ObservableLogger> _loggers = new ConcurrentDictionary<string, ObservableLogger>();
        private readonly Action<string> _logAction;

        public ObservableLoggerProvider(Action<string> logAction)
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