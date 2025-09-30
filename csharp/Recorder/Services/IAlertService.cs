using System;

namespace Recorder.Services
{
    public interface IAlertService
    {
        event Action<string> OnShowAlert;
        void ShowAlert(string message);
    }
}