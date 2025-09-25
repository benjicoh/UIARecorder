using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FlaUI.Core.Tools;
using FlaUI.UIA3;
using System;
using System.Drawing;

namespace FlaUI.Generated
{
    public static class AutomationElementExtensions
    {
        public static void Click(this AutomationElement element, int x, int y)
        {
            var bounds = element.BoundingRectangle;
            var clickPoint = new Point(bounds.Left + x, bounds.Top + y);
            Mouse.Click(clickPoint);
        }

        public static AutomationElement WaitFor(this AutomationElement element, string xpath, int milliseconds)
        {
            var result = Retry.WhileNull(() => element.FindFirstByXPath(xpath), TimeSpan.FromMilliseconds(milliseconds));
            if (result.Result == null)
            {
                throw new TimeoutException($"Could not find element with XPath: {xpath}");
            }
            return result.Result;
        }
    }

    public static class ApplicationExtensions
    {
        public static AutomationElement WaitFor(this Application app, UIA3Automation automation, string xpath, int milliseconds)
        {
            var timeout = TimeSpan.FromMilliseconds(milliseconds);
            // First, wait for the main window to appear.
            var mainWindow = app.GetMainWindow(automation, timeout);
            if (mainWindow == null)
            {
                throw new TimeoutException("Main window not found within the timeout period.");
            }
            // Then, wait for the element within the main window.
            return mainWindow.WaitFor(xpath, milliseconds);
        }
    }
}