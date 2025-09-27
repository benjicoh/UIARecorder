using FlaUI.Core.Input;
using OpenCvSharp;
using System;
using System.Collections.Generic;
using System.Drawing;
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
        private readonly List<Overlay> _overlays = new List<Overlay>();
        private readonly List<ClickOverlay> _clickOverlays = new List<ClickOverlay>();
        private readonly object _lock = new object();

        public void AddOverlay(Rectangle boundingBox, string text, Color color, DateTime timestamp)
        {
            lock (_lock)
            {
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
                var overlaysToDraw = _overlays.Where(o => Math.Abs((frameTimestamp - o.Timestamp).TotalSeconds) < 2).ToList();
                foreach (var overlay in overlaysToDraw)
                {
                    var rect = new OpenCvSharp.Rect(overlay.BoundingBox.X, overlay.BoundingBox.Y , overlay.BoundingBox.Width, overlay.BoundingBox.Height);
                    var color = new Scalar(overlay.Color.B, overlay.Color.G, overlay.Color.R, overlay.Color.A);
                    Cv2.Rectangle(image, rect, color, 2);
                    Cv2.PutText(image, overlay.Text, new OpenCvSharp.Point(rect.X + 5, rect.Y + 25), HersheyFonts.HersheySimplex, 0.5, color, 2);
                }

                var clicksToDraw = _clickOverlays.Where(c => Math.Abs((frameTimestamp - c.Timestamp).TotalSeconds) < 1).ToList();
                foreach (var click in clicksToDraw)
                {
                    var center = new OpenCvSharp.Point(click.Position.X , click.Position.Y);
                    var color = new Scalar(0, 255, 0); // Green for click

                    using var overlayMat = image.Clone();
                    Cv2.Circle(overlayMat, center, 15, color, -1);
                    double alpha = 0.4;
                    Cv2.AddWeighted(overlayMat, alpha, image, 1 - alpha, 0, image);
                }
            }
        }

        public void DrawCursor(Mat image)
        {
            var color = new Scalar(0, 0, 255); // Red color for the cursor
            int cursorSize = 10;
            var mousePosition = FlaUI.Core.Input.Mouse.Position;
            var center = new OpenCvSharp.Point(mousePosition.X, mousePosition.Y);

            // Ensure the cursor is drawn only if it's within the captured area
            if (center.X >= 0 && center.X < image.Width && center.Y >= 0 && center.Y < image.Height)
            {
                Cv2.Line(image, new OpenCvSharp.Point(center.X - cursorSize, center.Y), new OpenCvSharp.Point(center.X + cursorSize, center.Y), color, 2);
                Cv2.Line(image, new OpenCvSharp.Point(center.X, center.Y - cursorSize), new OpenCvSharp.Point(center.X, center.Y + cursorSize), color, 2);
            }
        }
    }
}