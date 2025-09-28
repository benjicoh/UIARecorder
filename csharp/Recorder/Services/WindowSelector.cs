using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using System;
using System.Diagnostics;
using System.Drawing;
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
        private HighlightWindow _highlightWindow; 
        private TaskCompletionSource<AutomationElement> _selectionTcs;

        public WindowSelector()
        {
            _automation = new UIA3Automation();
        }

        public Task<AutomationElement> SelectWindowAsync()
        {
            _selectionTcs = new TaskCompletionSource<AutomationElement>();

            
            _highlightWindow = new HighlightWindow();
            _highlightWindow.OnSelected += OnWindowSelected;
            _highlightWindow.Closed += OnWindowClosed;
            

            _timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
            _timer.Tick += UpdateHoveredWindow;
            _timer.Start();

            //_highlightWindow.Show();
            //_highlightWindow.Activate();
            return _selectionTcs.Task;
        }

        private void OnWindowSelected()
        {
            _selectionTcs?.TrySetResult(_currentHoveredWindow);
            // Cleanup is called because the HighlightWindow closes itself, which triggers OnWindowClosed.
        }

        private void OnWindowClosed(object sender, EventArgs e)
        {
            // If the task is already completed by a selection, this will be a no-op.
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
            if (_highlightWindow != null)
            {
                _highlightWindow.OnSelected -= OnWindowSelected;
                _highlightWindow.Closed -= OnWindowClosed;
                if (_highlightWindow.IsVisible)
                {
                    _highlightWindow.Close();
                }
                _highlightWindow = null;
            }
        }

        private void UpdateHoveredWindow(object sender, EventArgs e)
        {
            var cursorPosition = GetCursorPosition();
            var element = _automation.FromPoint(cursorPosition);

            var window = element?.AsWindow();
            if (window != null && window.Properties.BoundingRectangle.IsSupported)
            {
                // Ignore highlighting the highlight window itself or the main recorder window
                var windowProcId = window.Properties.ProcessId.ValueOrDefault;
                if (window.Name == "HighlightWindow" || windowProcId == Process.GetCurrentProcess().Id)
                {
                    return;
                }

                _currentHoveredWindow = window;
                var rect = window.Properties.BoundingRectangle.Value;
                _highlightWindow?.Highlight(rect);
            }
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