using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using Gma.System.MouseKeyHook;
using Microsoft.Extensions.Logging;
using Recorder.Models;
using Recorder.Utils;
using System;
using System.Drawing;
using System.Linq.Expressions;
using System.Windows.Forms;

namespace Recorder.Services
{
    public class InputUiaService : IDisposable
    {
        private readonly ILogger<InputUiaService> _logger;
        private readonly ThreadManager _threadManager;
        private readonly AnnotationService _annotationService;
        private readonly OverlayService _overlayService;
        private IKeyboardMouseEvents _globalHook;
        private UIA3Automation _automation;

        public InputUiaService(ILogger<InputUiaService> logger, ThreadManager threadManager, AnnotationService annotationService, OverlayService overlayService)
        {
            _logger = logger;
            _threadManager = threadManager;
            _annotationService = annotationService;
            _overlayService = overlayService;
        }

        public void Start()
        {
            _threadManager.InputUiaThread.EnqueueAction(() =>
            {
                _logger.LogInformation("Initializing Input/UIA service on dedicated thread.");
                _automation = new UIA3Automation();
                _globalHook = Hook.GlobalEvents();
                _globalHook.MouseDown += OnMouseDown;
                _globalHook.MouseUp += OnMouseUp;
                _globalHook.KeyUp += OnKeyUp;
            });
        }

        public void Stop()
        {
            _threadManager.InputUiaThread.EnqueueAction(() =>
            {
                _logger.LogInformation("Stopping Input/UIA service on dedicated thread.");
                if (_globalHook != null)
                {
                    _globalHook.MouseDown -= OnMouseDown;
                    _globalHook.MouseUp -= OnMouseUp;
                    _globalHook.KeyUp -= OnKeyUp;
                    _globalHook.Dispose();
                    _globalHook = null;
                }
                _automation?.Dispose();
                _automation = null;
            });
        }

        private void OnMouseDown(object sender, MouseEventArgs e)
        {
            OnMouseChange(e.X, e.Y, e.Button.ToString(), "Down");
        }

        private void OnMouseUp(object sender, MouseEventArgs e)
        {
            OnMouseChange(e.X, e.Y, e.Button.ToString(), "Up");
        }

        private void OnMouseChange(int x, int y,string button, string updown)
        {
            var ts = DateTime.UtcNow;
            _threadManager.InputUiaThread.EnqueueAction(() =>
            {
                try
                {
                    var element = _automation.FromPoint(new System.Drawing.Point(x, y));
                    if (element != null && element.GetSafeBoundingRectangle() != Rectangle.Empty)
                    {
                        var EventType = $"{button} {updown}";
                        var Coord = $"{x}, {y}";
                        _overlayService.AddClickOverlay(new OpenCvSharp.Point(x, y), EventType, ts);
                        _overlayService.AddOverlay(element.BoundingRectangle, element.GetIdentifier(), Color.Green, ts);

                        var elementInfo = GetElementHierarchy(element);
                        
                        _annotationService.AddEvent(elementInfo, "MouseClick", new { EventType, Coord }, ts);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error handling mouse click.");
                }
            });
        }

        private void OnKeyUp(object sender, KeyEventArgs e)
        {
            var ts = DateTime.UtcNow;
            _threadManager.InputUiaThread.EnqueueAction(() =>
            {
                try
                {
                    var element = _automation.FocusedElement();
                    if (element != null && element.GetSafeBoundingRectangle() != Rectangle.Empty)
                    {
                        _overlayService.AddOverlay(element.BoundingRectangle, element.GetIdentifier(), Color.Green, ts);

                        var elementInfo = GetElementHierarchy(element);
                        _annotationService.AddEvent(elementInfo, "KeyUp", new { e.KeyCode }, ts);
                    }
                }
                catch (Exception ex)
                {
                    _logger.LogError(ex, "Error handling key up.");
                }
            });
        }

        private ElementInfo GetElementHierarchy(AutomationElement element)
        {
            // This logic is extracted from the old UiaService
            if (element == null) return null;

            var hierarchy = new System.Collections.Generic.List<AutomationElement>();
            while (element != null)
            {
                hierarchy.Add(element);
                element = element.Parent;
            }
            hierarchy.Reverse();

            ElementInfo rootInfo = null;
            ElementInfo currentInfo = null;

            foreach (var el in hierarchy)
            {
                var newInfo = new ElementInfo
                {
                    AutomationID = el.GetSafeAutomationID(),
                    Name = el.GetSafeName(),
                    ControlType = el.GetSafeControlType(),
                    BoundingRectangle = el.GetSafeBoundingRectangle(),
                    Patterns = el.GetPatternsInfo()
                };

                if (rootInfo == null)
                {
                    rootInfo = newInfo;
                }
                else
                {
                    currentInfo.Children.Add(newInfo);
                }
                currentInfo = newInfo;
            }

            return rootInfo;
        }

        public void Dispose()
        {
            Stop();
        }
    }
}