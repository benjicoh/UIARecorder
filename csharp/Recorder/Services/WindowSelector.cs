using Gma.System.MouseKeyHook;
using Recorder.Utils;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Threading.Tasks;
using System.Windows.Forms;
using System.Windows.Threading;

namespace Recorder.Services
{
    public class WindowSelector : IDisposable
    {
        private DispatcherTimer _timer;
        private List<HighlightWindow> _highlightWindows = new List<HighlightWindow>();
        private IntPtr _currentHoveredWindow = IntPtr.Zero;
        private TaskCompletionSource<SelectionResult> _selectionTcs;
        private IKeyboardMouseEvents _globalHook;

        public WindowSelector()
        {
        }

        public Task<SelectionResult> SelectWindowAsync()
        {
            _globalHook = Hook.GlobalEvents();
            _globalHook.MouseDown += (s, e) =>
            {
                if (e.Button == MouseButtons.Left)
                {
                    OnWindowSelected();
                }
                else if (e.Button == MouseButtons.Right)
                {
                    OnWindowClosed(this, EventArgs.Empty);
                }
            };
            _selectionTcs = new TaskCompletionSource<SelectionResult>();
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
            if (_currentHoveredWindow != IntPtr.Zero)
            {
                Win32Utils.GetWindowRect(_currentHoveredWindow, out var rect);
                var area = new Rectangle(rect.Left, rect.Top, rect.Right - rect.Left, rect.Bottom - rect.Top);
                var result = new SelectionResult
                {
                    SelectedWindowHandle = _currentHoveredWindow,
                    WindowTitle = Win32Utils.GetWindowText(_currentHoveredWindow),
                    ProcessName = Win32Utils.GetProcessName(_currentHoveredWindow),
                    SelectedArea = area,
                    SelectedMonitor = Screen.AllScreens.ToList().IndexOf(Screen.FromHandle(_currentHoveredWindow))
                };
                _selectionTcs?.TrySetResult(result);
            }
            else
            {
                _selectionTcs?.TrySetResult(new SelectionResult()); // Indicate cancellation or failure
            }
            Cleanup();
        }

        private void OnWindowClosed(object sender, EventArgs e)
        {
            _selectionTcs?.TrySetResult(new SelectionResult());
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
            if (_globalHook != null)
            {
                _globalHook.Dispose();
                _globalHook = null;
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
            
            var windowRect = GetTopLevelWindow();
            var rect = new Rectangle(windowRect.Left, windowRect.Top, windowRect.Right - windowRect.Left, windowRect.Bottom - windowRect.Top);

            var screen = Screen.FromRectangle(rect);
            var highlightWindow = _highlightWindows.FirstOrDefault(w => w.Screen.DeviceName == screen.DeviceName);

            if (highlightWindow != null)
            {
                highlightWindow.Highlight(rect);
                foreach (var otherHw in _highlightWindows.Where(w => w != highlightWindow))
                {
                    otherHw.HideBorder();
                }
            }
            
            else
            {
                _highlightWindows.ForEach(w => w.HideBorder());
            }
        }

        private Win32Utils.Rect GetTopLevelWindow()
        {
            Win32Utils.GetCursorPos(out var pos);
            var handle = Win32Utils.WindowFromPoint(pos);
            while (handle != IntPtr.Zero && !Win32Utils.IsTopLevelWindow(handle))
            {
                handle = Win32Utils.GetParent(handle);
            }
            _currentHoveredWindow = handle;
            Win32Utils.GetWindowRect(handle, out var rect);
            return rect;
        }

        

        public void Dispose()
        {
            Cleanup();
        }
    }
}