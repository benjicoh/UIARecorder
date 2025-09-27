using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Conditions;
using FlaUI.UIA3;

namespace TestAutomationSuite
{
    public class Helpers
    {
        #region Win32 API Declarations
        [System.Runtime.InteropServices.DllImport("user32.dll")]
        [return: System.Runtime.InteropServices.MarshalAs(System.Runtime.InteropServices.UnmanagedType.Bool)]
        private static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
        [System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
        private static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);
        #endregion
        public static Window GetWindowByName(AutomationBase automation, Application app, string name)
        {
            var processId = app.ProcessId;
            var windows = GetAllTopLevelWindows(automation, processId);
            foreach (var window in windows)
            {
                try
                {
                    if (window.Name.Contains(name))
                    {
                        return window;
                    }
                }
                catch
                {
                }
            }
            return null;
        }

        public static Window GetWindowByAutomationID(AutomationBase automation, Application app, string automationId)
        {
            var processId = app.ProcessId;
            var windows = GetAllTopLevelWindows(automation, processId);
            foreach (var window in windows)
            {
                try
                {
                    if (window.AutomationId.Contains(automationId))
                    {
                        return window;
                    }
                }
                catch
                {
                }
            }
            return null;
        }
        //Get all top level windows by using win32 EnumWindows API
        public static Window[] GetAllTopLevelWindows(AutomationBase automation, string processName)
        {
            var process = System.Diagnostics.Process.GetProcessesByName(processName).FirstOrDefault();
            if (process == null)
            {
                throw new Exception($"Process '{processName}' not found.");
            }
            int ourProcessID = process.Id;
            return GetAllTopLevelWindows(automation, (nint)ourProcessID);
        }

        public static Window[] GetAllTopLevelWindows(AutomationBase automation, nint ourProcessID)
        {
            var windows = new List<Window>();
            EnumWindows((hWnd, lParam) =>
            {
                uint processId;
                GetWindowThreadProcessId(hWnd, out processId);
                if (processId == lParam)
                {
                    var w = automation.FromHandle(hWnd).AsWindow();
                    if (w != null)
                        windows.Add(w);
                }
                return true;
            }, ourProcessID);
            return windows.ToArray();
        }

    }
}