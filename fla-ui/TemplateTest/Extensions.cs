using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.Core.Input;
using FlaUI.Core.Tools;
using FlaUI.UIA3;
using System;
using System.Drawing;

namespace TestAutomationSuite
{
    public static class AutomationElementExtensions
    {
        public static void Click(this AutomationElement element, int x, int y, MouseButton button = MouseButton.Left, bool animate = true)
        {
            var bounds = element.BoundingRectangle;
            var clickPoint = new Point(bounds.Left + x, bounds.Top + y);
            if (animate)
            {
                Mouse.MoveTo(clickPoint);
            }
            Mouse.Click(clickPoint, button);
        }

        public static void DoubleClick(this AutomationElement element, int x, int y, MouseButton button = MouseButton.Left, bool animate = true)
        {
            var bounds = element.BoundingRectangle;
            var clickPoint = new Point(bounds.Left + x, bounds.Top + y);
            if (animate)
            {
                Mouse.MoveTo(clickPoint);
            }
            Mouse.DoubleClick(clickPoint, button);
        }

        public static void Drag(this AutomationElement element, Point start, Point end, bool animate = true)
        {
            var bounds = element.BoundingRectangle;
            var startPoint = new Point(bounds.Left + start.X, bounds.Top + start.Y);
            var endPoint = new Point(bounds.Left + end.X, bounds.Top + end.Y);
            if (animate)
            {
                Mouse.MoveTo(startPoint);
            }
            Mouse.Drag(startPoint, endPoint);
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

        public static void WaitForProperty<T>(this AutomationElement element, string propertyName, T expectedValue, int milliseconds)
        {
            var timeout = TimeSpan.FromMilliseconds(milliseconds);
            var startTime = DateTime.Now;
            while (DateTime.Now - startTime < timeout)
            {
                var propertyInfo = element.GetType().GetProperty(propertyName);
                if (propertyInfo == null)
                {
                    throw new ArgumentException($"Property '{propertyName}' not found on type '{element.GetType().Name}'");
                }
                var value = propertyInfo.GetValue(element);
                if (value != null && value.Equals(expectedValue))
                {
                    return;
                }
                System.Threading.Thread.Sleep(100);
            }
            throw new TimeoutException($"Property '{propertyName}' did not reach the expected value '{expectedValue}' within the timeout period.");
        }
    }

     public static class WindowExtensions
 {
       public static void Activate(this Window window)
     {
         var pattern = window.Patterns.Window?.Pattern;
         pattern?.SetWindowVisualState(FlaUI.Core.Definitions.WindowVisualState.Normal);
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