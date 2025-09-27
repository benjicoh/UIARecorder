using System.Diagnostics;
#if WINDOWS
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using ScreenRecorderLib;
#endif

namespace Recorder;

public partial class MainPage : ContentPage
{
#if WINDOWS
    private Recorder _recorder;
    private bool _isRecording = false;
#endif

    public MainPage()
    {
        InitializeComponent();
        App.OnHotkeyTriggered += HandleHotkey;
        this.Unloaded += (s, e) => App.OnHotkeyTriggered -= HandleHotkey;
        SourcePicker.SelectedIndex = 0; // Default to Desktop
    }

    private void HandleHotkey()
    {
        MainThread.BeginInvokeOnMainThread(() =>
        {
#if WINDOWS
            if (_isRecording)
            {
                OnStopClicked(this, EventArgs.Empty);
            }
            else
            {
                OnRecordClicked(this, EventArgs.Empty);
            }
#endif
        });
    }

    private void OnRecordClicked(object sender, EventArgs e)
    {
#if WINDOWS
        if (_isRecording) return;

        var recordingType = SourcePicker.SelectedItem as string ?? "Desktop";
        var outputFolder = Path.Combine(Path.GetTempPath(), "Recording_" + DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss"));
        Directory.CreateDirectory(outputFolder);
        var outputFile = Path.Combine(outputFolder, "video.mp4");

        var options = new RecorderOptions
        {
            VideoOptions = new VideoOptions
            {
                Bitrate = 8000 * 1000,
                Framerate = 30,
                IsMousePointerEnabled = true,
            }
        };

        Window windowToRecord = null;
        if (recordingType == "Window")
        {
            if (string.IsNullOrWhiteSpace(ProcessNameEntry.Text))
            {
                DisplayAlert("Error", "Process name is required for Window recording.", "OK");
                return;
            }
            windowToRecord = GetApplicationWindow(ProcessNameEntry.Text.Trim());
            if (windowToRecord == null)
            {
                DisplayAlert("Error", $"Could not find a window for process '{ProcessNameEntry.Text}'.", "OK");
                return;
            }
            options.VideoOptions.TargetWindowHandle = windowToRecord.Properties.NativeWindowHandle.Value;
        }
        else if (recordingType == "Region")
        {
             DisplayAlert("Not Implemented", "Region recording is not yet implemented.", "OK");
             return;
        }
        // else Desktop recording, no specific options needed here.

        // Dump UIA tree for the target window if specified, otherwise for the desktop.
        DumpUiaTree(windowToRecord, outputFolder);

        _recorder = Recorder.CreateRecorder(options);
        _recorder.OnRecordingComplete += OnRecordingComplete;
        _recorder.OnRecordingFailed += OnRecordingFailed;

        _recorder.Record(outputFile);

        SetRecordingState(true);
#else
        DisplayAlert("Unsupported", "Screen recording is only available on Windows.", "OK");
#endif
    }

    private void OnStopClicked(object sender, EventArgs e)
    {
#if WINDOWS
        if (!_isRecording) return;
        _recorder?.Stop();
#endif
    }

#if WINDOWS
    private void OnRecordingComplete(object sender, RecordingCompleteEventArgs e)
    {
        MainThread.BeginInvokeOnMainThread(() => SetRecordingState(false));
    }

    private void OnRecordingFailed(object sender, RecordingFailedEventArgs e)
    {
        MainThread.BeginInvokeOnMainThread(() =>
        {
            DisplayAlert("Error", $"Recording failed: {e.Error}", "OK");
            SetRecordingState(false);
        });
    }

    private void SetRecordingState(bool isRecording)
    {
        _isRecording = isRecording;
        RecordButton.IsEnabled = !isRecording;
        StopButton.IsEnabled = isRecording;
        SourcePicker.IsEnabled = !isRecording;
        ProcessNameEntry.IsEnabled = !isRecording;
    }

    private Window GetApplicationWindow(string processName)
    {
        var processes = Process.GetProcessesByName(processName);
        if (processes.Length == 0) return null;

        var process = processes.First(p => p.MainWindowHandle != IntPtr.Zero);
        if (process == null) return null;

        var app = FlaUI.Core.Application.Attach(process.Id);
        using (var automation = new UIA3Automation())
        {
            return app.GetMainWindow(automation);
        }
    }

    private void DumpUiaTree(Window window, string outputFolder)
    {
        var uiaDumpPath = Path.Combine(outputFolder, "uia_dump.xml");
        try
        {
            using (var automation = new UIA3Automation())
            {
                var element = window?.AsElement() ?? automation.GetDesktop();
                var xml = FlaUI.Core.Debug.GetXmlTree(element);
                File.WriteAllText(uiaDumpPath, xml);
            }
        }
        catch (Exception ex)
        {
            File.WriteAllText(uiaDumpPath, $"Error dumping UIA tree: {ex.Message}");
        }
    }
#endif
}