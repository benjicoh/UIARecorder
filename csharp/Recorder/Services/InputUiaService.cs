using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using Gma.System.MouseKeyHook;
using Microsoft.Extensions.Logging;
using Recorder.Models;
using Recorder.Utils;
using FlaUI.Core;
using FlaUI.Core.Exceptions;
using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows.Forms;
using Application = FlaUI.Core.Application;

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
        private Rectangle _captureArea;

        public InputUiaService(ILogger<InputUiaService> logger, ThreadManager threadManager, AnnotationService annotationService, OverlayService overlayService)
        {
            _logger = logger;
            _threadManager = threadManager;
            _annotationService = annotationService;
            _overlayService = overlayService;
        }

        public void Start(SelectionResult selection)
        {
            _captureArea = selection.SelectedArea;
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

        private void OnMouseChange(int x, int y, string button, string updown)
        {
            var screenPoint = new Point(x, y);
            if (!_captureArea.Contains(screenPoint))
            {
                return; // Ignore clicks outside the capture area
            }

            var ts = DateTime.UtcNow;
            _threadManager.InputUiaThread.EnqueueAction(() =>
            {
                try
                {
                    var element = _automation.FromPoint(screenPoint);
                    if (element != null && element.GetSafeBoundingRectangle() != Rectangle.Empty)
                    {
                        var relativePoint = CoordinateUtils.TransformFromScreen(screenPoint, _captureArea);
                        var EventType = $"{button} {updown}";
                        var Coord = $"{relativePoint.X}, {relativePoint.Y}";

                        _overlayService.AddClickOverlay(new OpenCvSharp.Point(relativePoint.X, relativePoint.Y), EventType, ts);
                        
                        var elementInfo = GetElementHierarchy(element);
                        if (elementInfo == null)
                        {
                            _logger.LogWarning("Could not retrieve element hierarchy for click at {X}, {Y}", x, y);
                            return;
                        }
                        _overlayService.AddOverlay(elementInfo.BoundingRectangle, element.GetIdentifier(), Color.Green, ts);
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
                        var elementInfo = GetElementHierarchy(element);
                        if (elementInfo == null)
                        {
                            _logger.LogWarning("Could not retrieve element hierarchy for key up event.");
                            return;
                        }
                        _overlayService.AddOverlay(elementInfo.BoundingRectangle, element.GetIdentifier(), Color.Green, ts);
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
                var screenRect = el.GetSafeBoundingRectangle();
                var intersection = Rectangle.Intersect(screenRect, _captureArea);

                if (rootInfo == null && intersection.IsEmpty)
                {
                    return null; // The main element is outside the capture area, ignore the hierarchy.
                }

                var relativeRect = new Rectangle(
                    screenRect.X - _captureArea.X,
                    screenRect.Y - _captureArea.Y,
                    screenRect.Width,
                    screenRect.Height
                );

                var newInfo = new ElementInfo
                {
                    AutomationID = el.GetSafeAutomationID(),
                    Name = el.GetSafeName(),
                    ControlType = el.GetSafeControlType(),
                    BoundingRectangle = relativeRect,
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

        public async Task<string> DumpUiTreeAsync(string processName)
        {
            return await Task.Run(() =>
            {
                try
                {
                    using (var automation = new UIA3Automation())
                    {
                        var app = FindApplication(processName);
                        if (app == null)
                        {
                            var message = "Application not found.";
                            _logger.LogWarning(message);
                            return message;
                        }

                        var window = app.GetMainWindow(automation);
                        if (window == null)
                        {
                            var message = "Main window not found.";
                            _logger.LogWarning(message);
                            return message;
                        }

                        var rootElement = BuildElementTree(window);
                        var options = new JsonSerializerOptions { WriteIndented = true };
                        var json = JsonSerializer.Serialize(rootElement, options);

                        return $"UI tree dumped successfully:\n```json\n{json}\n```";
                    }
                }
                catch (Exception ex)
                {
                    return $"Failed to dump UI tree: {ex.Message}";
                }
            });
        }

        private Application FindApplication(string processName)
        {
            if (!string.IsNullOrEmpty(processName))
            {
                var processes = Process.GetProcessesByName(processName);
                if (processes.Any())
                {
                    _logger.LogInformation("Found application by process name: {processName}", processName);
                    return Application.Attach(processes.First().Id);
                }
            }
            return null;
        }

        private ElementInfo BuildElementTree(AutomationElement element)
        {
            if (element == null) return null;

            var elementInfo = new ElementInfo
            {
                AutomationID = element.GetSafeAutomationID(),
                Name = element.GetSafeName(),
                ControlType = element.GetSafeControlType(),
                BoundingRectangle = element.GetSafeBoundingRectangle(),
                ClassName = element.GetSafeClassName(),
                IsEnabled = element.GetSafeIsEnabled(),
                IsOffscreen = element.GetSafeIsOffscreen(),
                Patterns = element.GetPatternsInfo()
            };

            try
            {
                foreach (var child in element.FindAllChildren())
                {
                    elementInfo.Children.Add(BuildElementTree(child));
                }
            }
            catch (PropertyNotSupportedException)
            {
                // Some elements do not support children, just ignore.
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Could not get children for element {elementName}", element.GetSafeName());
            }

            return elementInfo;
        }
    }
}