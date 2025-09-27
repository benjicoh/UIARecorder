using Gma.System.MouseKeyHook;
using Microsoft.Extensions.Logging;
using System;
using System.Windows.Forms;

namespace Recorder.Services
{
    public class TimestampedMouseEventArgs : MouseEventArgs
    {
        public DateTime Timestamp { get; }

        public TimestampedMouseEventArgs(MouseButtons button, int clicks, int x, int y, int delta, DateTime timestamp)
            : base(button, clicks, x, y, delta)
        {
            Timestamp = timestamp;
        }
    }

    public class TimestampedKeyEventArgs : KeyEventArgs
    {
        public DateTime Timestamp { get; }

        public TimestampedKeyEventArgs(Keys keyData, DateTime timestamp)
            : base(keyData)
        {
            Timestamp = timestamp;
        }
    }

    public class InputHookService : IDisposable
    {
        private readonly IKeyboardMouseEvents _globalHook;
        private readonly ILogger<InputHookService> _logger;

        public event EventHandler<TimestampedMouseEventArgs> MouseClick;
        public event EventHandler<TimestampedKeyEventArgs> KeyUp;

        public InputHookService(ILogger<InputHookService> logger)
        {
            _logger = logger;
            _globalHook = Hook.GlobalEvents();
        }

        public void Start()
        {
            _logger.LogInformation("Starting input hook service.");
            _globalHook.MouseClick += OnMouseClick;
            _globalHook.KeyUp += OnKeyUp;
        }

        public void Stop()
        {
            _logger.LogInformation("Stopping input hook service.");
            _globalHook.MouseClick -= OnMouseClick;
            _globalHook.KeyUp -= OnKeyUp;
        }

        private void OnMouseClick(object sender, MouseEventArgs e)
        {
            _logger.LogInformation("Mouse clicked at {Location}", e.Location);
            MouseClick?.Invoke(this, new TimestampedMouseEventArgs(e.Button, e.Clicks, e.X, e.Y, e.Delta, DateTime.UtcNow));
        }

        private void OnKeyUp(object sender, KeyEventArgs e)
        {
            _logger.LogInformation("Key up: {Key}", e.KeyCode);
            KeyUp?.Invoke(this, new TimestampedKeyEventArgs(e.KeyData, DateTime.UtcNow));
        }

        public void Dispose()
        {
            Stop();
            _globalHook?.Dispose();
        }
    }
}