using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.Logging;
using Recorder.Services;
using Recorder.Utils;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
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

        [ObservableProperty]
        private string projectDirectoryPath;

        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(IsNotGenerating))]
        private bool isGenerating;

        public bool IsNotGenerating => !isGenerating;

        public ObservableCollection<string> CaptureModes { get; }

        private readonly RecordingService _recordingService;
        private readonly InputUiaService _inputUiaService;
        private readonly AnnotationService _annotationService;
        private readonly ThreadManager _threadManager;
        private readonly ILogger<MainViewModel> _logger;
        private readonly IServiceProvider _serviceProvider;
        private readonly GeminiTestGenerator _geminiTestGenerator;

        public ObservableCollection<string> LogMessages { get; } = new ObservableCollection<string>();
        private SelectionResult _selectionRes = new SelectionResult();
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
            IServiceProvider serviceProvider,
            GeminiTestGenerator geminiTestGenerator)
        {
            _recordingService = recordingService;
            _inputUiaService = inputUiaService;
            _annotationService = annotationService;
            _threadManager = threadManager;
            _logger = logger;
            _serviceProvider = serviceProvider;
            _geminiTestGenerator = geminiTestGenerator;

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
            await Task.Delay(200); // Allow window to hide

            bool success = false;
            switch (SelectedCaptureMode)
            {
                case "Select Monitor":
                    _selectionRes = await ShowMonitorSelection();
                    if (_selectionRes.SelectedMonitor != -1)
                    {
                        CaptureAreaInfo = $"Monitor: {Screen.AllScreens[_selectionRes.SelectedMonitor].DeviceName} ({_selectionRes.SelectedArea.Width}x{_selectionRes.SelectedArea.Height})";
                        success = true;
                    }
                    break;
                case "Select Window":
                    var windowSelector = (WindowSelector)_serviceProvider.GetService(typeof(WindowSelector));
                    _selectionRes = await windowSelector.SelectWindowAsync();
                    if (_selectionRes.SelectedWindowHandle != IntPtr.Zero)
                    {
                        CaptureAreaInfo = $"Window: '{_selectionRes.WindowTitle}' ({_selectionRes.SelectedArea.Width}x{_selectionRes.SelectedArea.Height})";
                        success = true;
                    }
                    break;
                case "Select Region":
                    var selectedRegion = await ShowRegionSelectionAsync();
                    if (!selectedRegion.IsEmpty)
                    {
                        _selectionRes.SelectedArea = selectedRegion;
                        CaptureAreaInfo = $"Region ({_selectionRes.SelectedArea.Width}x{_selectionRes.SelectedArea.Height} at {_selectionRes.SelectedArea.Location})";
                        success = true;
                    }
                    break;
            }
            if (!success)
            {
                _selectionRes = new SelectionResult()   ;
                CaptureAreaInfo = "Selection cancelled.";
            }

            Application.Current.MainWindow.Show();
        }

        private async Task<SelectionResult> ShowMonitorSelection()
        {
            var selectionWindows = new List<MonitorSelectionWindow>();
            SelectionResult result = new SelectionResult();
            var manualResetEvent = new System.Threading.ManualResetEvent(false);
            int i = 0;
            foreach (var screen in ScreenHelper.GetAllScreens())
            {
                var selectionWindow = new MonitorSelectionWindow(screen, i );
                selectionWindows.Add(selectionWindow);
                selectionWindow.MouseDown += (s, e) =>
                {
                    var clickedWin = s as MonitorSelectionWindow;
                    if (clickedWin != null)
                    {
                        result.SelectedArea = clickedWin.SelectedArea;
                        result.SelectedMonitor = clickedWin.MonitorID;
                        foreach (var win in selectionWindows)
                        {
                            win.Close();
                        }

                    }

                    manualResetEvent.Set();
                };
                selectionWindow.Show();
                i++;

            }
            await Task.Run(() => manualResetEvent.WaitOne());
            return result;
        }

        private Task<Rectangle> ShowRegionSelectionAsync()
        {
            var tcs = new TaskCompletionSource<Rectangle>();
            var selectionWindows = new List<SelectionWindow>();

            foreach (var screen in ScreenHelper.GetAllScreens())
            {
                var selectionWindow = new SelectionWindow(screen);
                selectionWindows.Add(selectionWindow);

                selectionWindow.RegionSelected += (s, rect) =>
                {
                    tcs.TrySetResult(rect);
                    foreach (var win in selectionWindows)
                    {
                        win.Close();
                    }
                };

                selectionWindow.Show();
            }

            return tcs.Task;
        }


        [RelayCommand]
        private async Task ToggleRecording()
        {
            IsBusy = true;
            try
            {
                if (IsRecording) // We arrive here after clicking to start recording
                {
                    //if (_selectionRes.IsEmpty)
                    //{
                    //    _logger.LogWarning("Capture area not selected.");
                    //    System.Windows.MessageBox.Show("Please select a capture area before recording.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                    //    IsRecording = false;
                    //    return;
                    //}
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
                    _inputUiaService.Start(_selectionRes);
                    _recordingService.StartRecording(videoFilePath, _selectionRes);
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

        [RelayCommand]
        private void BrowseProjectDirectory()
        {
            using (var dialog = new FolderBrowserDialog())
            {
                dialog.Description = "Select the project directory";
                dialog.UseDescriptionForTitle = true;
                DialogResult result = dialog.ShowDialog();
                if (result == DialogResult.OK)
                {
                    ProjectDirectoryPath = dialog.SelectedPath;
                    _logger.LogInformation("Project directory selected: {path}", ProjectDirectoryPath);
                }
            }
        }

        [RelayCommand]
        private async Task GenerateTest()
        {
            if (string.IsNullOrEmpty(ProjectDirectoryPath))
            {
                System.Windows.MessageBox.Show("Please select a project directory first.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            if (string.IsNullOrEmpty(_annotationsFilePath))
            {
                 System.Windows.MessageBox.Show("Please record a scenario first.", "Warning", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }

            IsGenerating = true;
            try
            {
                _logger.LogInformation("Starting Gemini test generation...");
                string recordingDir = Path.GetDirectoryName(_annotationsFilePath);
                await _geminiTestGenerator.GenerateAndRunTestAsync(ProjectDirectoryPath, recordingDir, _selectionRes.ProcessName);
                _logger.LogInformation("Gemini test generation process completed.");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred during test generation.");
                System.Windows.MessageBox.Show($"An error occurred: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
            }
            finally
            {
                IsGenerating = false;
            }
        }
    }
}