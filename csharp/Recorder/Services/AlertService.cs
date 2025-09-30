using System;

namespace Recorder.Services
{
    public class AlertService : IAlertService
    {
        public event Action<string> OnShowAlert;

        public void ShowAlert(string message)
        {
            OnShowAlert?.Invoke(message);
        }
    }
}