using FFMpegCore;
using FFMpegCore.Enums;
using Microsoft.Extensions.Logging;
using NAudio.Wave;
using OpenCvSharp;
using Sdcb.ScreenCapture;
using System;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Threading.Tasks;

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

            var videoTask = Task.Run(() => RecordVideo(token, captureArea));
            var audioTask = Task.Run(() => RecordAudio(token));

            await Task.WhenAll(videoTask, audioTask);

            await MergeVideoAndAudio();
        }

        public void StopRecording()
        {
            _cancellationTokenSource?.Cancel();
        }

        private void RecordVideo(CancellationToken token, Rectangle captureArea)
        {
            try
            {
                CaptureVideoFrames(token, 20, captureArea);
            }
            catch (OperationCanceledException)
            {
                _logger.LogInformation("Video recording was canceled.");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "An error occurred during video recording.");
            }
        }

        private void CaptureVideoFrames(CancellationToken token, int frameRate, Rectangle captureArea)
        {
            var fourcc = FourCC.FromString("X264");
            using var writer = new VideoWriter(_tempVideoPath, fourcc, frameRate, new OpenCvSharp.Size(captureArea.Width, captureArea.Height));

            var captureOptions = new ScreenCaptureOptions
            {
                Region = captureArea,
            };

            foreach (var frame in ScreenCapture.CaptureScreenFrames(captureOptions, frameRate, token))
            {
                if (token.IsCancellationRequested)
                {
                    break;
                }

                using var mat = Mat.FromPixelData(frame.Height, frame.Width, MatType.CV_8UC4, frame.DataPointer);
                DrawOverlays(mat, captureArea.Location);
                writer.Write(mat);
            }
        }

        private void DrawOverlays(Mat image, Point captureOrigin)
        {
            var overlays = _overlayService.GetOverlays();
            foreach (var overlay in overlays)
            {
                var rect = new OpenCvSharp.Rect(overlay.BoundingBox.X - captureOrigin.X, overlay.BoundingBox.Y - captureOrigin.Y, overlay.BoundingBox.Width, overlay.BoundingBox.Height);
                var color = new Scalar(overlay.Color.B, overlay.Color.G, overlay.Color.R, overlay.Color.A);
                Cv2.Rectangle(image, rect, color, 2);
                Cv2.PutText(image, overlay.Text, new OpenCvSharp.Point(rect.X, rect.Y - 5), HersheyFonts.HersheySimplex, 0.5, color, 2);
            }

            var clickOverlays = _overlayService.GetClickOverlays();
            foreach (var click in clickOverlays)
            {
                var center = new OpenCvSharp.Point(click.Position.X - captureOrigin.X, click.Position.Y - captureOrigin.Y);
                var color = new Scalar(0, 0, 255); // Red

                using (var overlayMat = image.Clone())
                {
                    Cv2.Circle(overlayMat, center, 15, color, -1);
                    double alpha = 0.4;
                    Cv2.AddWeighted(overlayMat, alpha, image, 1 - alpha, 0, image);
                }
            }
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