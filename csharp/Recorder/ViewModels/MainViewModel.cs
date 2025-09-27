using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.Logging;
using Recorder.Services;
using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Threading.Tasks;
using System.Windows;

namespace Recorder.ViewModels
{
    public partial class MainViewModel : ObservableObject
    {
        [ObservableProperty]
        private bool isRecording;

        [ObservableProperty]
        [NotifyPropertyChangedFor(nameof(IsNotBusy))]
        private bool isBusy;
        public bool IsNotBusy => !isBusy;

        private readonly RecordingService _recordingService;
        private readonly ILogger<MainViewModel> _logger;
        public ObservableCollection<string> LogMessages { get; } = new ObservableCollection<string>();
        private Task _recordingTask;

        public MainViewModel(RecordingService recordingService, ILogger<MainViewModel> logger)
        {
            _recordingService = recordingService;
            _logger = logger;
        }

        [RelayCommand(CanExecute = nameof(IsNotBusy))]
        private async Task ToggleRecording()
        {
            IsBusy = true;
            try
            {
                if (IsRecording)
                {
                    var outputPath = Path.Combine("recordings", $"recording_{DateTime.Now:yyyyMMdd_HHmmss}.mp4");
                    _logger.LogInformation("Starting recording to {outputPath}", outputPath);

                    _recordingTask = Task.Run(async () =>
                    {
                        try
                        {
                            await _recordingService.StartRecordingAsync(outputPath);
                            _logger.LogInformation("Recording finished and file saved.");
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
                            Application.Current.Dispatcher.Invoke(() =>
                            {
                                IsRecording = false;
                            });
                        }
                    });
                }
                else
                {
                    _logger.LogInformation("Stopping recording...");

                    _recordingService.StopRecording();
                    if (_recordingTask != null)
                    {
                        await _recordingTask;
                    }

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