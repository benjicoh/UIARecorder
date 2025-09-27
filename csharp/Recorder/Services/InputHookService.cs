using Gma.System.MouseKeyHook;
using Microsoft.Extensions.Logging;
using System;
using System.Windows.Forms;

namespace Recorder.Services
{
    public class InputHookService : IDisposable
    {
        private readonly IKeyboardMouseEvents _globalHook;
        private readonly ILogger<InputHookService> _logger;

        public event EventHandler<MouseEventArgs> MouseClick;
        public event EventHandler<KeyEventArgs> KeyUp;

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
            MouseClick?.Invoke(this, e);
        }

        private void OnKeyUp(object sender, KeyEventArgs e)
        {
            _logger.LogInformation("Key up: {Key}", e.KeyCode);
            KeyUp?.Invoke(this, e);
        }

        public void Dispose()
        {
            Stop();
            _globalHook?.Dispose();
        }
    }
}