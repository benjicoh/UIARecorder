using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using Recorder.Utils;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Windows.Threading;

namespace Recorder.Services
{
    public class WindowSelector : IDisposable
    {
        private readonly UIA3Automation _automation;
        private DispatcherTimer _timer;
        private AutomationElement _currentHoveredWindow;
        private List<HighlightWindow> _highlightWindows = new List<HighlightWindow>();
        private TaskCompletionSource<AutomationElement> _selectionTcs;

        public WindowSelector()
        {
            _automation = new UIA3Automation();
        }

        public Task<AutomationElement> SelectWindowAsync()
        {
            _selectionTcs = new TaskCompletionSource<AutomationElement>();

            foreach (var screen in ScreenHelper.GetAllScreens())
            {
                var highlightWindow = new HighlightWindow(screen);
                highlightWindow.OnSelected += OnWindowSelected;
                highlightWindow.Closed += OnWindowClosed;
                _highlightWindows.Add(highlightWindow);
                highlightWindow.Show();
            }

            _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
            _timer.Tick += UpdateHoveredWindow;
            _timer.Start();

            return _selectionTcs.Task;
        }

        private void OnWindowSelected()
        {
            _selectionTcs?.TrySetResult(_currentHoveredWindow);
            Cleanup();
        }

        private void OnWindowClosed(object sender, EventArgs e)
        {
            _selectionTcs?.TrySetResult(null);
            Cleanup();
        }

        private void Cleanup()
        {
            if (_timer != null)
            {
                _timer.Stop();
                _timer.Tick -= UpdateHoveredWindow;
                _timer = null;
            }

            foreach (var hw in _highlightWindows)
            {
                hw.OnSelected -= OnWindowSelected;
                hw.Closed -= OnWindowClosed;
                if (hw.IsVisible)
                {
                    hw.Close();
                }
            }
            _highlightWindows.Clear();
        }

        private void UpdateHoveredWindow(object sender, EventArgs e)
        {
            var cursorPosition = GetCursorPosition();
            var element = _automation.FromPoint(cursorPosition);

            if (element == null)
            {
                _highlightWindows.ForEach(w => w.Hide());
                return;
            }

            var window = GetTopLevelWindow(element);

            if (window != null && window.Properties.BoundingRectangle.IsSupported)
            {
                var windowProcId = window.Properties.ProcessId.ValueOrDefault;
                if (window.Name.StartsWith("HighlightWindow") || windowProcId == Process.GetCurrentProcess().Id)
                {
                    _highlightWindows.ForEach(w => w.Hide());
                    return;
                }

                _currentHoveredWindow = window;
                var rect = window.Properties.BoundingRectangle.Value;

                var screen = Screen.FromRectangle(rect);
                var highlightWindow = _highlightWindows.FirstOrDefault(w => w.Screen.DeviceName == screen.DeviceName);

                if (highlightWindow != null)
                {
                    highlightWindow.Highlight(rect);
                    foreach (var otherHw in _highlightWindows.Where(w => w != highlightWindow))
                    {
                        otherHw.Hide();
                    }
                }
            }
            else
            {
                _highlightWindows.ForEach(w => w.Hide());
            }
        }

        private AutomationElement GetTopLevelWindow(AutomationElement element)
        {
            AutomationElement parent = element;
            while (parent.Parent != null && parent.Parent.GetType() != typeof(FlaUI.UIA3.UIA3AutomationElement))
            {
                parent = parent.Parent;
            }
            return parent.AsWindow();
        }

        private static Point GetCursorPosition()
        {
            GetCursorPos(out var lpPoint);
            return lpPoint;
        }

        [DllImport("user32.dll")]
        private static extern bool GetCursorPos(out POINT lpPoint);

        [StructLayout(LayoutKind.Sequential)]
        private struct POINT
        {
            public int X;
            public int Y;

            public static implicit operator Point(POINT point)
            {
                return new Point(point.X, point.Y);
            }
        }

        public void Dispose()
        {
            Cleanup();
        }
    }
}