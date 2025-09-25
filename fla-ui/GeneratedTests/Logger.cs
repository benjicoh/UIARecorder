using System;

namespace FlaUI.Generated
{
    public static class Logger
    {
        public static void LogInfo(string message, [System.Runtime.CompilerServices.CallerFilePath] string file = "", [System.Runtime.CompilerServices.CallerLineNumber] int line = 0)
        {
            Log(message, "INFO", ConsoleColor.Gray, file, line);
        }

        public static void LogWarning(string message, [System.Runtime.CompilerServices.CallerFilePath] string file = "", [System.Runtime.CompilerServices.CallerLineNumber] int line = 0)
        {
            Log(message, "WARNING", ConsoleColor.Yellow, file, line);
        }

        public static void LogError(string message, [System.Runtime.CompilerServices.CallerFilePath] string file = "", [System.Runtime.CompilerServices.CallerLineNumber] int line = 0)
        {
            Log(message, "ERROR", ConsoleColor.Red, file, line);
        }

        public static void LogPassed(string message, [System.Runtime.CompilerServices.CallerFilePath] string file = "", [System.Runtime.CompilerServices.CallerLineNumber] int line = 0)
        {
            Log(message, "!Passed!", ConsoleColor.Green, file, line);
        }

        public static void LogFailed(string message, [System.Runtime.CompilerServices.CallerFilePath] string file = "", [System.Runtime.CompilerServices.CallerLineNumber] int line = 0)
        {
            Log(message, "Failed", ConsoleColor.Red, file, line);
        }

        private static void Log(string message, string level, ConsoleColor color, string file, int line)
        {
            var originalColor = Console.ForegroundColor;
            Console.ForegroundColor = color;
            Console.WriteLine($"{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff} {System.IO.Path.GetFileName(file)}:{line} {level} {message}");
            Console.ForegroundColor = originalColor;
        }
    }
}