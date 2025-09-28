using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.Logging;
using Recorder.Services;
using System;
using System.Collections.ObjectModel;
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
        private bool isRecording;

        [ObservableProperty]
        private string outputPath;

        [ObservableProperty]
        private bool isBusy;

        [ObservableProperty]
        private string selectedCaptureMode;

        public ObservableCollection<string> CaptureModes { get; }

        private readonly RecordingService _recordingService;
        private readonly InputUiaService _inputUiaService;
        private readonly AnnotationService _annotationService;
        private readonly ThreadManager _threadManager;
        private readonly ILogger<MainViewModel> _logger;

        public ObservableCollection<string> LogMessages { get; } = new ObservableCollection<string>();
        private Rectangle _captureArea;
        private string _annotationsFilePath;

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

            CaptureModes = new ObservableCollection<string>
            {
                "Fullscreen",
                "Select Window",
                "Select Region"
            };
            SelectedCaptureMode = CaptureModes[0];
        }

        private bool SetCaptureArea()
        {
            Application.Current.MainWindow.WindowState = WindowState.Minimized;
            try
            {
                switch (SelectedCaptureMode)
                {
                    case "Fullscreen":
                        _captureArea = SystemInformation.VirtualScreen;
                        return true;
                    case "Select Window":
                        var windowSelection = new SelectionWindow(SelectionWindow.SelectionMode.Window);
                        if (windowSelection.ShowDialog() == true)
                        {
                            _captureArea = windowSelection.SelectedArea;
                            return !_captureArea.IsEmpty;
                        }
                        return false;
                    case "Select Region":
                        var regionSelection = new SelectionWindow(SelectionWindow.SelectionMode.Region);
                        if (regionSelection.ShowDialog() == true)
                        {
                            _captureArea = regionSelection.SelectedArea;
                            return !_captureArea.IsEmpty;
                        }
                        return false;
                    default:
                        return false;
                }
            }
            finally
            {
                //Application.Current.MainWindow.WindowState = WindowState.Normal;
            }
        }

        [RelayCommand]
        private async Task ToggleRecording()
        {
            IsBusy = true;
            try
            {
                if (IsRecording) // We arrive here after clicking to start recording
                {
                    if (!SetCaptureArea())
                    {
                        IsRecording = false; // Revert state if capture is cancelled
                        return;
                    }

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
                    _inputUiaService.Start();
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
                }
            }
            finally
            {
                IsBusy = false;
            }
        }
    }
}