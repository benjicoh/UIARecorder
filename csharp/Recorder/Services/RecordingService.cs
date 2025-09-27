using FFMpegCore;
using FFMpegCore.Enums;
using Microsoft.Extensions.Logging;
using NAudio.Wave;
using OpenCvSharp;
using Recorder.Models;
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
        private readonly ConcurrentQueue<FrameData> _frameQueue = new ConcurrentQueue<FrameData>();

        public RecordingService(ILogger<RecordingService> logger, OverlayService overlayService)
        {
            _logger = logger;
            _overlayService = overlayService;
        }

        public async Task StartRecordingAsync(string outputPath, Rectangle captureArea)
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

            var videoTask = RecordVideo(token, captureArea);
            var audioTask = Task.Run(() => RecordAudio(token));

            await Task.WhenAll(videoTask, audioTask);

            await MergeVideoAndAudio();
        }

        public void StopRecording()
        {
            _cancellationTokenSource?.Cancel();
        }

        private async Task RecordVideo(CancellationToken token, Rectangle captureArea)
        {
            var captureTask = CaptureFramesAsync(token);
            var processTask = ProcessFramesAsync(token, 20);

            await Task.WhenAll(captureTask, processTask);
        }

        private Task CaptureFramesAsync(CancellationToken token)
        {
            return Task.Run(() =>
            {
                try
                {
                    foreach (var frame in ScreenCapture.CaptureScreenFrames(0, 20.0, 0, token))
                    {
                        if (token.IsCancellationRequested) break;
                        var mat = Mat.FromPixelData(frame.Height, frame.Width, MatType.CV_8UC4, frame.DataPointer);
                        _overlayService.DrawCursor(mat);
                        _frameQueue.Enqueue(new FrameData(mat, DateTime.UtcNow));
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
            }, token);
        }

        private Task ProcessFramesAsync(CancellationToken token, int frameRate)
        {
            return Task.Run(() =>
            {
                var fourcc = FourCC.FromString("X264");
                var rect = ScreenCapture.GetScreenSize(0);
                using var writer = new VideoWriter(_tempVideoPath, fourcc, frameRate, new OpenCvSharp.Size(rect.Width, rect.Height));

                while (!token.IsCancellationRequested || !_frameQueue.IsEmpty)
                {
                    if (_frameQueue.TryDequeue(out var frameData))
                    {
                        using (var frame = frameData.Frame)
                        {
                            _overlayService.DrawOverlays(frame, frameData.Timestamp);
                            writer.Write(frame);
                        }
                    }
                    else
                    {
                        Task.Delay(10).Wait();
                    }
                }
            }, token);
        }

        private async Task RecordAudio(CancellationToken token)
        {
            try
            {
                using var waveIn = new WaveInEvent();
                waveIn.WaveFormat = new WaveFormat(44100, 1);
                using var writer = new WaveFileWriter(_tempAudioPath, waveIn.WaveFormat);

                var tcs = new TaskCompletionSource<bool>();

                waveIn.DataAvailable += (s, e) =>
                {
                    writer.Write(e.Buffer, 0, e.BytesRecorded);
                };

                waveIn.RecordingStopped += (s, e) =>
                {
                    writer.Flush();
                    tcs.TrySetResult(true);
                };

                using (token.Register(() => waveIn.StopRecording()))
                {
                    waveIn.StartRecording();
                    await tcs.Task;
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred during audio recording. This may happen if no microphone is available.");
            }
        }

        private async Task MergeVideoAndAudio()
        {
            bool videoExists = File.Exists(_tempVideoPath);
            bool audioExists = File.Exists(_tempAudioPath) && new FileInfo(_tempAudioPath).Length > 0;

            if (videoExists && audioExists)
            {
                await FFMpegArguments
                    .FromFileInput(_tempVideoPath)
                    .AddFileInput(_tempAudioPath)
                    .OutputToFile(_outputPath, true, options => options
                        .CopyChannel()
                        .WithVideoCodec(VideoCodec.LibX264)
                        .WithAudioCodec(AudioCodec.Aac)
                        .WithFastStart())
                    .ProcessAsynchronously();

                File.Delete(_tempVideoPath);
                File.Delete(_tempAudioPath);
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