#if WINDOWS
using Microsoft.UI;
using Microsoft.UI.Windowing;
using Recorder.Platforms.Windows;
using System.Runtime.InteropServices;
#endif

namespace Recorder;

public partial class App : Application
{
    public static event Action OnHotkeyTriggered;

#if WINDOWS
    private int _hotkeyId;
    private delegate IntPtr WndProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
    private WndProc _newWndProc;
    private IntPtr _oldWndProc;
#endif

    public App()
    {
        InitializeComponent();
        MainPage = new AppShell();
    }

    protected override Window CreateWindow(IActivationState activationState)
    {
        var window = base.CreateWindow(activationState);

#if WINDOWS
        var nativeWindow = window.Handler.PlatformView as MauiWinUIWindow;
        if (nativeWindow != null)
        {
            var windowHandle = nativeWindow.WindowHandle;
            _hotkeyId = HotkeyManager.Register(windowHandle, KeyModifier.Alt | KeyModifier.Shift, VirtualKey.R, () =>
            {
                 OnHotkeyTriggered?.Invoke();
            });

            _newWndProc = new WndProc(NewWindowProc);
            _oldWndProc = PInvoke.User32.SetWindowLongPtr(windowHandle, PInvoke.User32.WindowLongIndexFlags.GWL_WNDPROC, Marshal.GetFunctionPointerForDelegate(_newWndProc));
        }

        window.Destroying += (s, e) =>
        {
            if (_hotkeyId != -1)
            {
                HotkeyManager.Unregister(_hotkeyId);
            }
            if(_oldWndProc != IntPtr.Zero)
            {
                 var windowHandle = (s as Window)?.Handler.PlatformView.GetType().GetProperty("WindowHandle")?.GetValue(s.Handler.PlatformView) as IntPtr? ?? IntPtr.Zero;
                 if(windowHandle != IntPtr.Zero)
                 {
                    PInvoke.User32.SetWindowLongPtr(windowHandle, PInvoke.User32.WindowLongIndexFlags.GWL_WNDPROC, _oldWndProc);
                 }
            }
        };
#endif

        return window;
    }

#if WINDOWS
    private IntPtr NewWindowProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam)
    {
        const int WM_HOTKEY = 0x0312;
        if (msg == WM_HOTKEY)
        {
            HotkeyManager.ProcessHotkey(wParam.ToInt32());
        }
        return PInvoke.User32.CallWindowProc(_oldWndProc, hWnd, msg, wParam, lParam);
    }
#endif
}