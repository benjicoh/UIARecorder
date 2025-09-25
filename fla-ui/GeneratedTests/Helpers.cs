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
}