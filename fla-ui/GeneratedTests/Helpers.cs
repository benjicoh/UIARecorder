using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Conditions;
using FlaUI.UIA3;

namespace FlaUI.Generated
{
    public class Helpers
    {
        public static Window GetWindowByName(AutomationBase automation, Application app, string name)
        {
            var windows = app.GetAllTopLevelWindows(automation);
            foreach (var window in windows)
            {
                if (window.Name.Contains(name))
                {
                    return window;
                }
                var foundWindow = window.FindFirstDescendant(cf => cf.ByName(name)).AsWindow();
                if (foundWindow != null)
                {
                    return foundWindow;
                }
            }
            return null;
        }

        public static Window GetWindowByAutomationID(AutomationBase automation, Application app, string automationId)
        {
            var windows = app.GetAllTopLevelWindows(automation);
            foreach (var window in windows)
            {
                if (window.AutomationId.Contains(automationId))
                {
                    return window;
                }
                var foundWindow = window.FindFirstDescendant(cf => cf.ByAutomationId(automationId)).AsWindow();
                if (foundWindow != null)
                {
                    return foundWindow;
                }
            }
            return null;
        }


    }

    //Generate a logging class in the format of <DateTime> <File:Line> <Level> <Message>
    //The console color should be different for each level
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