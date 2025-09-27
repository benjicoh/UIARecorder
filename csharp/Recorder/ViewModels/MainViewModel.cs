using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.Logging;
using Recorder.Services;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Drawing;
using System.IO;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Forms;
using Application = System.Windows.Application;
using FlaUI.Core.AutomationElements;

namespace Recorder.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        [ObservableProperty]
        private bool isRecording;

        [ObservableProperty]
        private bool isBusy;

        [ObservableProperty]
        private string selectedCaptureMode;

        public ObservableCollection<string> CaptureModes { get; }

        private readonly RecordingService _recordingService;
        private readonly InputHookService _inputHookService;
        private readonly UiaService _uiaService;
        private readonly OverlayService _overlayService;
        private readonly AnnotationService _annotationService;
        private readonly ILogger<MainViewModel> _logger;

        public ObservableCollection<string> LogMessages { get; } = new ObservableCollection<string>();
        private Task _recordingTask;
        private Rectangle _captureArea;

        public MainViewModel(
            RecordingService recordingService,
            InputHookService inputHookService,
            UiaService uiaService,
            OverlayService overlayService,
            AnnotationService annotationService,
            ILogger<MainViewModel> logger)
        {
            _recordingService = recordingService;
            _inputHookService = inputHookService;
            _uiaService = uiaService;
            _overlayService = overlayService;
            _annotationService = annotationService;
            _logger = logger;

            CaptureModes = new ObservableCollection<string>
            {
                "Fullscreen",
                "Select Window",
                "Select Region"
            };
            SelectedCaptureMode = CaptureModes[0];

            _inputHookService.MouseClick += OnMouseClick;
            _inputHookService.KeyUp += OnKeyUp;
        }

        private void OnMouseClick(object sender, TimestampedMouseEventArgs e)
        {
            App.StartSTATask(() =>
            {
                var element = _uiaService.GetElementFromPoint(e.Location);
                ElementInfo hierarchy = null;
                if (element != null)
                {
                    hierarchy = _uiaService.GetElementHierarchy(element);

                    var colors = new[] { Color.Red, Color.Blue, Color.Green, Color.Yellow, Color.Orange, Color.Magenta };
                    int i = 0;
                    if (!hierarchy.BoundingRectangle.IsEmpty)
                    {
                        _overlayService.AddOverlay(hierarchy.BoundingRectangle, hierarchy.GetIdentifier(), colors[i++ % colors.Length], e.Timestamp);
                    }
                    hierarchy = hierarchy.Parent;
                }
                var location = new OpenCvSharp.Point(e.Location.X, e.Location.Y);
                _overlayService.AddClickOverlay(location, e.Button.ToString(), e.Timestamp);
                _annotationService.AddAnnotation(EventType.MouseClick, new { e.X, e.Y, Button = e.Button.ToString() }, hierarchy);
            });
        }

        private void OnKeyUp(object sender, TimestampedKeyEventArgs e)
        {
            App.StartSTATask(() =>
            {
                var element = _uiaService.GetFocusedElement();
                ElementInfo hierarchy = null;
                if (element != null)
                {
                    hierarchy = _uiaService.GetElementHierarchy(element);

                    var colors = new[] { Color.Red, Color.Blue, Color.Green, Color.Yellow, Color.Orange, Color.Magenta };
                    int i = 0;

                    if (!hierarchy.BoundingRectangle.IsEmpty)
                    {
                        var rect = hierarchy.BoundingRectangle;
                        _overlayService.AddOverlay(rect, hierarchy.GetIdentifier(), colors[i++ % colors.Length], e.Timestamp);
                    }
                    hierarchy = hierarchy.Parent;
                }
                _annotationService.AddAnnotation(EventType.KeyPress, new { Key = e.KeyCode.ToString() }, hierarchy);
            });
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
                Application.Current.MainWindow.WindowState = WindowState.Normal;
            }
        }

        [RelayCommand]
        private async Task ToggleRecording()
        {
            IsBusy = true;
            try
            {
                if (!IsRecording) // Start recording
                {
                    if (!SetCaptureArea())
                    {
                        return;
                    }

                    IsRecording = true;

                    var recordingId = $"recording_{DateTime.Now:yyyyMMdd_HHmmss}";
                    var outputPath = Path.Combine("recordings", recordingId);
                    Directory.CreateDirectory(outputPath);
                    var videoFilePath = Path.Combine(outputPath, "video.mp4");
                    var annotationsFilePath = Path.Combine(outputPath, "annotations.json");

                    _logger.LogInformation("Starting recording to {outputPath}", outputPath);

                    _annotationService.Start();
                    _inputHookService.Start();

                    _recordingTask = Task.Run(async () =>
                    {
                        try
                        {
                            await _recordingService.StartRecordingAsync(videoFilePath, _captureArea);
                        }
                        catch (OperationCanceledException)
                        {
                            _logger.LogInformation("Recording process was cancelled.");
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError(ex, "An error occurred during recording.");
                        }
                        finally
                        {
                            await _annotationService.StopAndSaveAsync(annotationsFilePath);
                            _inputHookService.Stop();
                            _overlayService.ClearOverlays();
                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                IsRecording = false;
                            });
                        }
                    });
                }
                else // Stop recording
                {
                    _logger.LogInformation("Stopping recording...");
                    _recordingService.StopRecording();
                    if (_recordingTask != null)
                    {
                        await _recordingTask;
                    }
                    _logger.LogInformation("Recording stopped.");
                    IsRecording = false;
                }
            }
            finally
            {
                IsBusy = false;
            }
        }
    }
}