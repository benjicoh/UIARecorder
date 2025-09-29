using FlaUI.Core.Capturing;
using FlaUI.Core.Input;
using OpenCvSharp;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Windows.Input;
using Point = OpenCvSharp.Point;

namespace Recorder.Services
{
    public class Overlay
    {
        public Rectangle BoundingBox { get; set; }
        public string Text { get; set; }
        public Color Color { get; set; }

        public DateTime Timestamp { get; set; }
    }

    public class ClickOverlay
    {
        public Point Position { get; set; }
        public string Button { get; set; }
        public DateTime Timestamp { get; set; }
    }

    public class OverlayService
    {
        private static List<Scalar> colors = new List<Scalar>
        {
            new Scalar(255, 0, 0), // Blue
            new Scalar(0, 255, 0), // Green
            new Scalar(0, 0, 255), // Red
            new Scalar(255, 255, 0), // Cyan
            new Scalar(255, 0, 255), // Magenta
            new Scalar(0, 255, 255), // Yellow
            new Scalar(255, 165, 0), // Orange
            new Scalar(128, 0, 128), // Purple
            new Scalar(0, 128, 128), // Teal
            new Scalar(128, 128, 0)  // Olive
        };

        private readonly List<Overlay> _overlays = new List<Overlay>();
        private readonly List<ClickOverlay> _clickOverlays = new List<ClickOverlay>();
        private readonly object _lock = new object();

        public void AddOverlay(Rectangle boundingBox, string text, Color color, DateTime timestamp)
        {
            lock (_lock)
            {
                //sanitize text as ansi
                text = string.Concat(text.Where(c => c >= 32 && c <= 126));
                _overlays.Add(new Overlay { BoundingBox = boundingBox, Text = text, Color = color, Timestamp = timestamp });
            }
        }

        public void AddClickOverlay(Point position, string button, DateTime timestamp)
        {
            lock (_lock)
            {
                _clickOverlays.Add(new ClickOverlay { Position = position, Button = button, Timestamp = timestamp });
            }
        }

        
        public void DrawOverlays(Mat image, DateTime frameTimestamp)
        {
            lock (_lock)
            {
                //filter overlays from 250 ms before operation till 1.5 seconds after
                var overlaysToDraw = _overlays.Where(o => (frameTimestamp - o.Timestamp).TotalSeconds > -0.25 && (frameTimestamp - o.Timestamp).TotalSeconds < 1.5).ToList();
                int i = 0;
                var black = new Scalar(0, 0, 0);
                foreach (var overlay in overlaysToDraw)
                {
                    var rect = new OpenCvSharp.Rect(overlay.BoundingBox.X, overlay.BoundingBox.Y, overlay.BoundingBox.Width, overlay.BoundingBox.Height);
                    var color = colors[i++ % colors.Count];
                    //move 3,3 and draw black for better visibility
                    var shiftRect = new OpenCvSharp.Rect(rect.X + 1, rect.Y + 1, rect.Width, rect.Height);
                    Cv2.Rectangle(image, shiftRect, black, 2);
                    Cv2.Rectangle(image, rect, color, 2);
                    
                    Cv2.PutText(image, overlay.Text, new OpenCvSharp.Point(rect.X + 6, rect.Y + 26), HersheyFonts.HersheySimplex, 0.5, black, 2, LineTypes.AntiAlias);
                    Cv2.PutText(image, overlay.Text, new OpenCvSharp.Point(rect.X + 5, rect.Y + 25), HersheyFonts.HersheySimplex, 0.5, color, 2, LineTypes.AntiAlias);
                }

                var clicksToDraw = _clickOverlays.Where(o => (frameTimestamp - o.Timestamp).TotalSeconds > -0.25 && (frameTimestamp - o.Timestamp).TotalSeconds < 0.75).ToList();
                using var overlayMat = image.Clone();
                foreach (var click in clicksToDraw)
                {
                    var center = new OpenCvSharp.Point(click.Position.X, click.Position.Y);
                    //Magenta for left click, Cyan for right click
                    var color = click.Button.Contains("Left") ? new Scalar(255, 0, 255) : new Scalar(255, 255, 0);
                    //darken if contains up
                    if (click.Button.Contains("Up"))
                    {
                        color = new Scalar(color.Val0 * 0.5, color.Val1 * 0.5, color.Val2 * 0.5);
                    }


                    Cv2.Circle(overlayMat, center, 15, color, -1);
                    double alpha = 0.4;
                    Cv2.AddWeighted(overlayMat, alpha, image, 1 - alpha, 0, image);
                }
            }
        }

        public void DrawCursor(Mat image, System.Drawing.Point offset = default)
        {
            var color = new Scalar(0, 0, 255); // Red color for the cursor
            int cursorSize = 10;
            var mousePosition = FlaUI.Core.Input.Mouse.Position;

            // Adjust cursor position based on the offset of the captured region
            var center = new OpenCvSharp.Point(mousePosition.X - offset.X, mousePosition.Y - offset.Y);

            // Ensure the cursor is drawn only if it's within the captured area
            if (center.X >= 0 && center.X < image.Width && center.Y >= 0 && center.Y < image.Height)
            {
                Cv2.Line(image, new OpenCvSharp.Point(center.X - cursorSize, center.Y), new OpenCvSharp.Point(center.X + cursorSize, center.Y), color, 2);
                Cv2.Line(image, new OpenCvSharp.Point(center.X, center.Y - cursorSize), new OpenCvSharp.Point(center.X, center.Y + cursorSize), color, 2);
            }
        }

        internal string AddOverlayToVideo(string tempVideoPath, DateTime startCaptureTime)
        {
            using var capture = new VideoCapture(tempVideoPath);
            var copiedVideoPath = tempVideoPath.Replace(".mp4", "_with_overlays.mp4");
            using var writer = new VideoWriter(copiedVideoPath, FourCC.FromString("X264"), capture.Fps, new OpenCvSharp.Size(capture.FrameWidth, capture.FrameHeight));
            if (!capture.IsOpened())
            {
                throw new Exception("Failed to open video file for overlay processing.");
            }
            using var frame = new Mat(); // Mat object to store each frame
            int frameCount = 0;
            while (true)
            {
                capture.Read(frame); // Read the next frame into the 'frame' Mat
                var frameTimestamp = startCaptureTime.AddSeconds(frameCount / capture.Fps);
                DrawOverlays(frame, frameTimestamp);
                writer.Write(frame); // Write the processed frame to the new video file

                frameCount++;
                if (frame.Empty()) // Check if the frame is empty (end of video)
                {
                    break;
                }
            }
            capture.Release();
            //delete the original temp video
            File.Delete(tempVideoPath);
            return copiedVideoPath;
        }
    }
}