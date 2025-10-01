using FFMpegCore;
using FFMpegCore.Enums;
using Microsoft.Extensions.Logging;
using NAudio.Wave;
using OpenCvSharp;
using Recorder.Models;
using Recorder.Utils;
using Sdcb;
using System;
using System.Collections.Concurrent;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Point = System.Drawing.Point;

namespace Recorder.Services
{
    public class RecordingService
    {
        private CancellationTokenSource _cancellationTokenSource;
        private string _tempVideoPath;
        private string _tempAudioPath;
        private string _outputPath;
        private readonly ILogger<RecordingService> _logger;
        private readonly OverlayService _overlayService;
        private readonly ThreadManager _threadManager;
        private readonly ConcurrentQueue<FrameData> _frameQueue = new ConcurrentQueue<FrameData>();
        private DateTime _startCaptureTime;

        public RecordingService(ILogger<RecordingService> logger, OverlayService overlayService, ThreadManager threadManager)
        {
            _logger = logger;
            _overlayService = overlayService;
            _threadManager = threadManager;
        }

        public void StartRecording(string outputPath, SelectionResult selection)
        {
            _cancellationTokenSource = new CancellationTokenSource();
            var token = _cancellationTokenSource.Token;
            _outputPath = outputPath;

            var outputDir = Path.GetDirectoryName(outputPath);
            if (!string.IsNullOrEmpty(outputDir))
            {
                Directory.CreateDirectory(outputDir);
            }

            _tempVideoPath = Path.Combine(outputDir, Guid.NewGuid() + ".mp4");
            _tempAudioPath = Path.Combine(outputDir, Guid.NewGuid() + ".wav");

            _threadManager.VideoCaptureThread.EnqueueAction(() => RecordVideo(token, selection));
            _threadManager.AudioCaptureThread.EnqueueAction(() => RecordAudio(token));
        }

        public void StopRecording()
        {
            try
            {
                _cancellationTokenSource?.Cancel();
                _threadManager.StopAll(); // Ensure all threads are stopped
                _logger.LogInformation("Post processing video...");
                _tempVideoPath = _overlayService.AddOverlayToVideo(_tempVideoPath, _startCaptureTime);
                MergeVideoAndAudio();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred while stopping the recording.");
            }
            finally
            {
                _cancellationTokenSource?.Dispose();
                _cancellationTokenSource = null;
            }
        }

        private void RecordVideo(CancellationToken token, SelectionResult selection)
        {
            // This method is executed on the VideoCaptureThread.
            // We kick off processing on its own thread and start capturing frames directly.
            //_threadManager.VideoProcessingThread.EnqueueAction(() => ProcessFrames(token, 20));
            CaptureFrames(token, selection);
        }

        private void CaptureFrames(CancellationToken token, SelectionResult selection)
        {
            try
            {
                selection.MakeDivisableBy2();
                var rect = selection.SelectedArea;
                
                var screenSize = ScreenCapture.GetScreenSize(selection.SelectedMonitor);
                var fullScreenRect = new Rectangle(0, 0, screenSize.Width, screenSize.Height);

                if (rect == Rectangle.Empty || !fullScreenRect.Contains(rect))
                {
                    rect = fullScreenRect;
                }
                bool shouldCrop = rect != fullScreenRect;


                using var writer = new VideoWriter(_tempVideoPath, FourCC.X264, 20.0, new OpenCvSharp.Size(rect.Width, rect.Height));
                if (!writer.IsOpened())
                {
                    _logger.LogError("Could not open video writer.");
                    return;
                }
                _startCaptureTime = DateTime.UtcNow;

                foreach (var frame in ScreenCapture.CaptureScreenFrames(selection.SelectedMonitor, 20.0, 0, token))
                {
                    if (token.IsCancellationRequested) break;

                    using var fullScreenMat = Mat.FromPixelData(frame.Height, frame.Width, MatType.CV_8UC4, frame.DataPointer);

                    if (shouldCrop)
                    {

                        // Adjust the rect to be within the bounds of the full screen mat
                        var cropRect = new OpenCvSharp.Rect(
                            Math.Max(0, rect.X),
                            Math.Max(0, rect.Y),
                            Math.Min(rect.Width, fullScreenMat.Width - rect.X),
                            Math.Min(rect.Height, fullScreenMat.Height - rect.Y)
                        );

                        using var croppedMat = new Mat(fullScreenMat, cropRect);
                        _overlayService.DrawCursor(croppedMat, new Point(rect.X, rect.Y));
                        writer.Write(croppedMat);
                    }
                    else
                    {
                        _overlayService.DrawCursor(fullScreenMat);
                        writer.Write(fullScreenMat);
                    }
                }
            }
            catch (OperationCanceledException)
            {
                _logger.LogInformation("Frame capture was canceled.");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred during frame capture.");
            }
        }

        private void RecordAudio(CancellationToken token)
        {
            try
            {
                using var waveIn = new WaveInEvent();
                waveIn.WaveFormat = new WaveFormat(44100, 1);
                using var writer = new WaveFileWriter(_tempAudioPath, waveIn.WaveFormat);

                waveIn.DataAvailable += (s, e) =>
                {
                    writer.Write(e.Buffer, 0, e.BytesRecorded);
                };

                waveIn.RecordingStopped += (s, e) =>
                {
                    _logger.LogInformation("Audio recording stopped.");
                    try
                    {
                        writer.Flush();
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError(ex, "Problem flushing audio");
                    }
                };

                using (token.Register(() => waveIn.StopRecording()))
                {
                    _logger.LogInformation("Starting audio recording.");
                    waveIn.StartRecording();
                    while (!token.IsCancellationRequested)
                    {
                        Thread.Sleep(100);
                    }
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred during audio recording. This may happen if no microphone is available.");
            }
        }

        private void MergeVideoAndAudio()
        {
            bool videoExists = File.Exists(_tempVideoPath);
            bool audioExists = File.Exists(_tempAudioPath) && new FileInfo(_tempAudioPath).Length > 0;
            _logger.LogInformation($"Merging video and audio. Video exists: {videoExists}, Audio exists: {audioExists}");
            if (videoExists && audioExists)
            {
                FFMpegArguments
                    .FromFileInput(_tempVideoPath)
                    .AddFileInput(_tempAudioPath)
                    .OutputToFile(_outputPath, true, options => options
                        .CopyChannel()
                        .WithVideoCodec(VideoCodec.LibX264)
                        .WithAudioCodec(AudioCodec.Aac)
                        .WithFastStart())
                    .ProcessSynchronously();

                File.Delete(_tempVideoPath);
                File.Delete(_tempAudioPath);
                _logger.LogInformation($"Merged video and audio saved to {_outputPath}");
            }
            else if (videoExists)
            {
                File.Move(_tempVideoPath, _outputPath);
            }
            else if (audioExists)
            {
                File.Delete(_tempAudioPath);
            }
        }
    }
}