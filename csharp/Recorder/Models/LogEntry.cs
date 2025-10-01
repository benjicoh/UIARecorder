using Microsoft.Extensions.Logging;
using System;

namespace Recorder.Models
{
    public class LogEntry
    {
        public DateTime Timestamp { get; set; }
        public LogLevel Level { get; set; }
        public string Message { get; set; }
        public string CallerFilePath { get; set; }
        public int CallerLineNumber { get; set; }
        public string CallerMemberName { get; set; }

        public Exception Exception { get; set; }


        public LogEntry(LogLevel level, string message, string callerFilePath, int callerLineNumber, string callerMemberName, Exception exception)
        {
            Timestamp = DateTime.Now;
            Level = level;
            Message = message;
            CallerFilePath = callerFilePath;
            CallerLineNumber = callerLineNumber;
            CallerMemberName = callerMemberName;
            Exception = exception;
        }

        public override string ToString()
        {
            var file = System.IO.Path.GetFileName(CallerFilePath);
            return $"{Timestamp:yyyy-MM-dd HH:mm:ss} - {Level} [{file}:{CallerLineNumber}] - {Message} {Exception?.Message}";
        }
    }
}