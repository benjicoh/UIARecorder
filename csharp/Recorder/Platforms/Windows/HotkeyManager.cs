using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;

namespace Recorder.Platforms.Windows
{
    public static class HotkeyManager
    {
        [DllImport("user32.dll")]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

        [DllImport("user32.dll")]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        private static int _currentId = 0;
        private static readonly Dictionary<int, (IntPtr hWnd, Action action)> _hotkeys = new();

        public static int Register(IntPtr windowHandle, KeyModifier fsModifiers, VirtualKey vk, Action action)
        {
            var id = _currentId++;
            if (!RegisterHotKey(windowHandle, id, (uint)fsModifiers, (uint)vk))
            {
                // Handle error, maybe throw an exception
                return -1;
            }
            _hotkeys[id] = (windowHandle, action);
            return id;
        }

        public static void Unregister(int id)
        {
            if (_hotkeys.TryGetValue(id, out var hotkey))
            {
                UnregisterHotKey(hotkey.hWnd, id);
                _hotkeys.Remove(id);
            }
        }

        public static void ProcessHotkey(int id)
        {
            if (_hotkeys.TryGetValue(id, out var hotkey))
            {
                hotkey.action?.Invoke();
            }
        }
    }

    [Flags]
    public enum KeyModifier
    {
        None = 0,
        Alt = 1,
        Control = 2,
        Shift = 4,
        WinKey = 8
    }

    public enum VirtualKey
    {
        R = 0x52
    }
}