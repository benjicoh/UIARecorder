using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using Gma.System.MouseKeyHook;
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

        [StructLayout(LayoutKind.Sequential)]
        private struct RECT
        {
            public int Left;
            public int Top;
            public int Right;
            public int Bottom;
        }

        //window from point
        [DllImport("user32.dll")]
        private static extern IntPtr WindowFromPoint(Point pt);
        //get top level window from child window
        [DllImport("user32.dll")]
        private static extern IntPtr GetAncestor(IntPtr hwnd, uint gaFlags);
        private const uint GA_ROOT = 2;
        //parent window
        [DllImport("user32.dll")]
        private static extern IntPtr GetParent(IntPtr hWnd);

        //get bounding rectangle
        [DllImport("user32.dll")]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        //get window long
        [DllImport("user32.dll", SetLastError = true)]
        private static extern IntPtr GetWindowLong(IntPtr hWnd, int nIndex);

        //is top level
        private const int GWL_STYLE = -16;
        private const int WS_CHILD = 0x40000000;
        
        private static bool IsTopLevelWindow(IntPtr hWnd)
        {
            IntPtr style = GetWindowLong(hWnd, GWL_STYLE);
            return (style.ToInt64() & WS_CHILD) == 0;
        }

        private DispatcherTimer _timer;
        private List<HighlightWindow> _highlightWindows = new List<HighlightWindow>();
        private IntPtr _currentHoveredWindow = IntPtr.Zero;
        private TaskCompletionSource<IntPtr> _selectionTcs;
        private IKeyboardMouseEvents _globalHook;

        public WindowSelector()
        {
        }

        public Task<IntPtr> SelectWindowAsync()
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
            _selectionTcs = new TaskCompletionSource<IntPtr>();
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
            _selectionTcs?.TrySetResult(IntPtr.Zero);
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

        private RECT GetTopLevelWindow()
        {
            var pos = GetCursorPosition();
            var handle = WindowFromPoint(pos);
            while (handle != IntPtr.Zero && !IsTopLevelWindow(handle))
            {
                handle = GetParent(handle);
            }
            _currentHoveredWindow = handle;
            GetWindowRect(handle, out var rect);
            return rect;
        }

        private static Point GetCursorPosition()
        {
            GetCursorPos(out var lpPoint);
            return lpPoint;
        }

        

        public void Dispose()
        {
            Cleanup();
        }
    }
}