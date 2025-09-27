using FFMpegCore;
using FFMpegCore.Enums;
using Microsoft.Extensions.Logging;
using NAudio.Wave;
using OpenCvSharp;
using Sdcb;
using System;
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

            var videoTask = App.StartSTATask(() => RecordVideo(token, captureArea));
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


            foreach (var frame in ScreenCapture.CaptureScreenFrames(0, (double)frameRate, 0, token))
            {
                if (token.IsCancellationRequested)
                {
                    break;
                }

                using var mat = Mat.FromPixelData(frame.Height, frame.Width, MatType.CV_8UC4, frame.DataPointer);
                var location = new OpenCvSharp.Point(captureArea.X, captureArea.Y);
                _overlayService.DrawOverlays(mat, location);
                writer.Write(mat);
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