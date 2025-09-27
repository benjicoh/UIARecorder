using FFMpegCore;
using FFMpegCore.Pipes;
using NAudio.Wave;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Sdcb.ScreenCapture;
using FFMpegCore.Enums;
using Microsoft.Extensions.Logging;

namespace Recorder.Services
{
    public class RecordingService
    {
        private CancellationTokenSource _cancellationTokenSource;
        private string _tempVideoPath;
        private string _tempAudioPath;
        private string _outputPath;
        private readonly ILogger<RecordingService> _logger;

        public RecordingService(ILogger<RecordingService> logger)
        {
            _logger = logger;
        }

        public async Task StartRecordingAsync(string outputPath)
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

            var videoTask = RecordVideo(token);
            var audioTask = RecordAudio(token);

            await Task.WhenAll(videoTask, audioTask);

            await MergeVideoAndAudio();
        }

        public void StopRecording()
        {
            _cancellationTokenSource?.Cancel();
        }

        private async Task RecordVideo(CancellationToken token)
        {
            try
            {
                var frameRate = 20;
                var videoFrames = GetVideoFrames(token, frameRate);

                await FFMpegArguments
                    .FromPipeInput(new RawVideoPipeSource(videoFrames), options => options.WithFramerate(frameRate))
                    .OutputToFile(_tempVideoPath, true, options => options
                        .WithVideoCodec(VideoCodec.LibX264)
                        .WithVideoBitrate(2000)
                        .WithFastStart())
                    .ProcessAsynchronously(true, token);
            }
            catch (OperationCanceledException)
            {
                _logger.LogInformation("Video recording was canceled.");
            }
        }

        private IEnumerable<IVideoFrame> GetVideoFrames(CancellationToken token, int frameRate)
        {
            foreach (var frame in ScreenCapture.CaptureScreenFrames(0, frameRate, 0, token))
            {
                if (token.IsCancellationRequested)
                {
                    yield break;
                }

                var bmp = new Bitmap(frame.Width, frame.Height, frame.RowPitch, System.Drawing.Imaging.PixelFormat.Format32bppArgb, frame.DataPointer);
                yield return new BitmapVideoFrameWrapper(bmp);
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
                        .WithVideoCodec(VideoCodec.Copy)
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

            if(audioExists && !videoExists)
            {
                File.Delete(_tempAudioPath);
            }
        }
    }
}