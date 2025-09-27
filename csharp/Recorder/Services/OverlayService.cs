using System;
using System.Collections.Generic;
using System.Drawing;

namespace Recorder.Services
{
    public class Overlay
    {
        public Rectangle BoundingBox { get; set; }
        public string Text { get; set; }
        public Color Color { get; set; }
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

        public void AddOverlay(Rectangle boundingBox, string text, Color color)
        {
            lock (_lock)
            {
                _overlays.Add(new Overlay { BoundingBox = boundingBox, Text = text, Color = color });
            }
        }

        public void AddClickOverlay(Point position, string button)
        {
            lock (_lock)
            {
                _clickOverlays.Add(new ClickOverlay { Position = position, Button = button, Timestamp = DateTime.UtcNow });
            }
        }

        public void ClearOverlays()
        {
            lock (_lock)
            {
                _overlays.Clear();
            }
        }

        public List<Overlay> GetOverlays()
        {
            lock (_lock)
            {
                return new List<Overlay>(_overlays);
            }
        }

        public List<ClickOverlay> GetClickOverlays()
        {
            lock (_lock)
            {
                // Remove old click overlays
                _clickOverlays.RemoveAll(c => (DateTime.UtcNow - c.Timestamp).TotalSeconds > 1);
                return new List<ClickOverlay>(_clickOverlays);
            }
        }
    }
}