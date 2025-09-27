using System;
using System.Runtime.InteropServices;

internal static partial class PInvoke
{
    internal static partial class User32
    {
        [DllImport("user32.dll", SetLastError = true)]
        internal static extern IntPtr GetWindowLongPtr(IntPtr hWnd, WindowLongIndexFlags nIndex);

        [DllImport("user32.dll", SetLastError = true)]
        internal static extern IntPtr SetWindowLongPtr(IntPtr hWnd, WindowLongIndexFlags nIndex, IntPtr dwNewLong);

        [DllImport("user32.dll")]
        internal static extern IntPtr CallWindowProc(IntPtr lpPrevWndFunc, IntPtr hWnd, uint uMsg, IntPtr wParam, IntPtr lParam);

        internal enum WindowLongIndexFlags
        {
            GWL_WNDPROC = -4,
        }
    }
}