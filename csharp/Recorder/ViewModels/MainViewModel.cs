using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using Microsoft.Extensions.Logging;
using Recorder.Services;
using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Forms;
using System.Windows.Threading;
using Application = System.Windows.Application;
using Point = System.Drawing.Point;

namespace Recorder.ViewModels
{
    public partial class MainViewModel : ObservableObject, IDisposable
    {
        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(TrayToolTipText))]
        [NotifyPropertyChangedFor(nameof(IsNotRecording))]
        private bool isRecording;

        public bool IsNotRecording => !IsRecording;

        [ObservableProperty]
        private string outputPath;

        [ObservableProperty]
        private bool isBusy;

        [ObservableProperty]
        private string selectedCaptureMode;

        [ObservableProperty]
        private string captureAreaInfo;

        public ObservableCollection<string> CaptureModes { get; }

        private readonly RecordingService _recordingService;
        private readonly InputUiaService _inputUiaService;
        private readonly AnnotationService _annotationService;
        private readonly ThreadManager _threadManager;
        private readonly ILogger<MainViewModel> _logger;

        private Rectangle _captureArea;
        private string _annotationsFilePath;

        private DispatcherTimer _highlightTimer;
        private HighlightWindow _highlightWindow;
        private UIA3Automation _automation;
        private Rectangle _currentHighlightArea;

        public string TrayToolTipText => IsRecording
            ? "Recording is in progress. Press Alt+Shift+R to stop."
            : "Recorder is idle. Press Alt+Shift+R to start.";

        public MainViewModel(
            RecordingService recordingService,
            InputUiaService inputUiaService,
            AnnotationService annotationService,
            ThreadManager threadManager,
            ILogger<MainViewModel> logger)
        {
            _recordingService = recordingService;
            _inputUiaService = inputUiaService;
            _annotationService = annotationService;
            _threadManager = threadManager;
            _logger = logger;
            _automation = new UIA3Automation();

            CaptureModes = new ObservableCollection<string>
            {
                "Select Monitor",
                "Select Window",
                "Select Region"
            };
            SelectedCaptureMode = CaptureModes[0];
        }

        [RelayCommand]
        private async Task SelectCaptureArea()
        {
            Application.Current.MainWindow.Hide();
            await Task.Delay(200); // Give time for window to hide

            try
            {
                bool success = false;
                switch (SelectedCaptureMode)
                {
                    case "Select Monitor":
                    case "Select Window":
                        _captureArea = await SelectWithHighlightAsync(SelectedCaptureMode);
                        if (!_captureArea.IsEmpty)
                        {
                            if (SelectedCaptureMode == "Select Monitor")
                            {
                                var screen = Screen.AllScreens.First(s => s.Bounds == _captureArea);
                                CaptureAreaInfo = $"Monitor: {screen.DeviceName} ({_captureArea.Width}x{_captureArea.Height})";
                            }
                            else // Select Window
                            {
                                CaptureAreaInfo = $"Window ({_captureArea.Width}x{_captureArea.Height} at {_captureArea.Location})";
                            }
                            success = true;
                        }
                        break;
                    case "Select Region":
                        var selectionViewModel = new SelectionViewModel();
                        var regionSelection = new SelectionWindow(selectionViewModel);
                        if (regionSelection.ShowDialog() == true)
                        {
                            _captureArea = regionSelection.SelectedArea;
                            if (!_captureArea.IsEmpty)
                            {
                                CaptureAreaInfo = $"Region ({_captureArea.Width}x{_captureArea.Height} at {_captureArea.Location})";
                                success = true;
                            }
                        }
                        break;
                }

                if (!success)
                {
                    _captureArea = Rectangle.Empty;
                    CaptureAreaInfo = "Selection cancelled.";
                }
            }
            finally
            {
                Application.Current.MainWindow.Show();
                Application.Current.MainWindow.Activate();
            }
        }

        private Task<Rectangle> SelectWithHighlightAsync(string mode)
        {
            var tcs = new TaskCompletionSource<Rectangle>();
            _highlightWindow = new HighlightWindow();

            _highlightTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(100) };
            _highlightTimer.Tick += (s, e) => UpdateHighlight(mode);

            _highlightWindow.OnSelected += () =>
            {
                _highlightTimer.Stop();
                tcs.TrySetResult(_currentHighlightArea);
            };

            _highlightWindow.Closed += (s, e) =>
            {
                _highlightTimer?.Stop();
                tcs.TrySetResult(Rectangle.Empty); // Cancellation
                _highlightWindow = null;
            };

            _highlightTimer.Start();
            _highlightWindow.ShowDialog();

            return tcs.Task;
        }

        private void UpdateHighlight(string mode)
        {
            var cursorPosition = GetCursorPosition();
            Rectangle rectToHighlight = Rectangle.Empty;

            if (mode == "Select Monitor")
            {
                var screen = Screen.AllScreens.FirstOrDefault(s => s.Bounds.Contains(cursorPosition));
                if (screen != null)
                {
                    rectToHighlight = screen.Bounds;
                }
            }
            else // Select Window
            {
                var element = _automation.FromPoint(cursorPosition);
                var window = element?.AsWindow();

                if (window != null && window.Properties.BoundingRectangle.IsSupported)
                {
                    var windowProcId = window.Properties.ProcessId.ValueOrDefault;
                    if (windowProcId != Process.GetCurrentProcess().Id)
                    {
                        rectToHighlight = window.BoundingRectangle;
                    }
                }
            }

            _currentHighlightArea = rectToHighlight;
            _highlightWindow?.Highlight(_currentHighlightArea);
        }


        [RelayCommand]
        private async Task ToggleRecording()
        {
            IsBusy = true;
            try
            {
                if (!IsRecording) // START
                {
                    if (_captureArea.IsEmpty)
                    {
                        _logger.LogWarning("Capture area not selected.");
                        MessageBox.Show("Please select a capture area before recording.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                        return;
                    }
                    IsRecording = true;
                    Application.Current.MainWindow.WindowState = WindowState.Minimized;

                    string finalOutputPath;
                    if (!string.IsNullOrEmpty(OutputPath))
                    {
                        finalOutputPath = OutputPath;
                    }
                    else
                    {
                        var recordingId = $"recording_{DateTime.Now:yyyyMMdd_HHmmss}";
                        finalOutputPath = Path.Combine("recordings", recordingId);
                    }

                    Directory.CreateDirectory(finalOutputPath);
                    var videoFilePath = Path.Combine(finalOutputPath, "video.mp4");
                    _annotationsFilePath = Path.Combine(finalOutputPath, "annotations.json");

                    _logger.LogInformation("Starting recording to {outputPath}", finalOutputPath);

                    _threadManager.StartAll();
                    _annotationService.Start();
                    _inputUiaService.Start(_captureArea);
                    _recordingService.StartRecording(videoFilePath, _captureArea);
                }
                else // STOP
                {
                    IsRecording = false; // Set this early to update UI
                    _logger.LogInformation("Stopping recording...");

                    await Task.Run(async () =>
                    {
                        _inputUiaService.Stop();
                        _recordingService.StopRecording();
                        await _annotationService.StopAndSaveAsync(_annotationsFilePath);
                    });

                    _logger.LogInformation("Recording stopped.");
                    Application.Current.MainWindow.WindowState = WindowState.Normal;
                    Application.Current.MainWindow.Activate();
                }
            }
            finally
            {
                IsBusy = false;
            }
        }

        [RelayCommand]
        private void ShowWindow()
        {
            var window = Application.Current.MainWindow;
            if (window.IsVisible)
            {
                window.Hide();
            }
            else
            {
                window.Show();
                if (window.WindowState == WindowState.Minimized)
                {
                    window.WindowState = WindowState.Normal;
                }
                window.Activate();
            }
        }

        [RelayCommand]
        private void ExitApplication()
        {
            Application.Current.Shutdown();
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
            _automation?.Dispose();
        }
    }
}