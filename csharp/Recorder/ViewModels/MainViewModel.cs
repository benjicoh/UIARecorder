using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.Logging;
using Recorder.Services;
using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Forms;
using Application = System.Windows.Application;

namespace Recorder.ViewModels
{
    public partial class MainViewModel : ObservableObject
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
        private readonly IServiceProvider _serviceProvider;

        public ObservableCollection<string> LogMessages { get; } = new ObservableCollection<string>();
        private Rectangle _captureArea;
        private string _annotationsFilePath;

        public string TrayToolTipText => IsRecording
            ? "Recording is in progress. Press Alt+Shift+R to stop."
            : "Recorder is idle. Press Alt+Shift+R to start.";

        public MainViewModel(
            RecordingService recordingService,
            InputUiaService inputUiaService,
            AnnotationService annotationService,
            ThreadManager threadManager,
            ILogger<MainViewModel> logger,
            IServiceProvider serviceProvider)
        {
            _recordingService = recordingService;
            _inputUiaService = inputUiaService;
            _annotationService = annotationService;
            _threadManager = threadManager;
            _logger = logger;
            _serviceProvider = serviceProvider;

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

            bool success = false;
            switch (SelectedCaptureMode)
            {
                case "Select Monitor":
                    var monitorSelection = new MonitorSelectionWindow();
                    if (monitorSelection.ShowDialog() == true)
                    {
                        _captureArea = monitorSelection.SelectedMonitor;
                        if (!_captureArea.IsEmpty)
                        {
                            //var screen = Screen.AllScreens.First(s => s.Bounds == _captureArea);
                            //CaptureAreaInfo = $"Monitor: {screen.DeviceName} ({_captureArea.Width}x{_captureArea.Height})";
                            success = true;
                        }
                    }
                    break;
                case "Select Window":
                    var windowSelector = (WindowSelector)_serviceProvider.GetService(typeof(WindowSelector));
                    var selectedWindow = await windowSelector.SelectWindowAsync();
                    if (selectedWindow != null)
                    {
                        _captureArea = selectedWindow.BoundingRectangle;
                        var processId = selectedWindow.Properties.ProcessId.ValueOrDefault;
                        var processName = Process.GetProcessById(processId).ProcessName;
                        CaptureAreaInfo = $"Window: '{selectedWindow.Name}' ({processName}, {_captureArea.Width}x{_captureArea.Height})";
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
            Application.Current.MainWindow.Show();


        }

        [RelayCommand]
        private async Task ToggleRecording()
        {
            IsBusy = true;
            try
            {
                if (IsRecording) // We arrive here after clicking to start recording
                {
                    if (_captureArea.IsEmpty)
                    {
                        _logger.LogWarning("Capture area not selected.");
                        System.Windows.MessageBox.Show("Please select a capture area before recording.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                        IsRecording = false;
                        return;
                    }
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
    }
}