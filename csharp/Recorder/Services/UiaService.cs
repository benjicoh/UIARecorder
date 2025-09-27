using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Recorder.Services
{
    public class UiaService
    {
        private readonly UIA3Automation _automation;

        public UiaService()
        {
            _automation = new UIA3Automation();
        }

        public AutomationElement GetElementFromPoint(Point screenPosition)
        {
            return _automation.FromPoint(screenPosition);
        }

        public AutomationElement GetFocusedElement()
        {
            return _automation.GetFocusedElement();
        }

        public List<Dictionary<string, object>> GetElementHierarchy(AutomationElement element)
        {
            var hierarchy = new List<Dictionary<string, object>>();
            var current = element;
            int depth = 0;
            while (current != null && current.FrameworkId != "WPF" && depth < 5) // Limit depth to avoid deep dives
            {
                var elementInfo = new Dictionary<string, object>
                {
                    ["id"] = current.AutomationId,
                    ["name"] = current.Name,
                    ["control_type"] = current.ControlType.ToString(),
                    ["bounding_rectangle"] = current.Properties.BoundingRectangle.Value
                };
                hierarchy.Add(elementInfo);
                current = current.Parent;
                depth++;
            }
            return hierarchy;
        }
    }
}