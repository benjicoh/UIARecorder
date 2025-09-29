using FlaUI.Core.AutomationElements;
using Recorder.Models;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Xml.Linq;

namespace Recorder.Utils
{
    public static class AutomationElementExtensions
    {
        public static string GetSafeAutomationID(this AutomationElement element)
        {
            try
            {
                return element.AutomationId;
            }
            catch
            {
                return string.Empty;
            }
        }

        public static string GetSafeName(this AutomationElement element)
        {
            try
            {
                return element.Name;
            }
            catch
            {
                return string.Empty;
            }
        }
        public static string GetSafeControlType(this AutomationElement element)
        {
            try
            {
                return element.ControlType.ToString();
            }
            catch
            {
                return string.Empty;
            }
        }
        public static Rectangle GetSafeBoundingRectangle(this AutomationElement element)
        {
            try
            {
                return element.Properties.BoundingRectangle.Value;
            }
            catch
            {
                return Rectangle.Empty;
            }
        }

        public static string GetSafeClassName(this AutomationElement element)
        {
            try
            {
                return element.Properties.ClassName.Value;
            }
            catch
            {
                return string.Empty;
            }
        }

        public static bool GetSafeIsEnabled(this AutomationElement element)
        {
            try
            {
                return element.Properties.IsEnabled.Value;
            }
            catch
            {
                return false;
            }
        }

        public static bool GetSafeIsOffscreen(this AutomationElement element)
        {
            try
            {
                return element.Properties.IsOffscreen.Value;
            }
            catch
            {
                return true; // Assume it's offscreen if property is not available
            }
        }

        public static List<PatternInfo> GetPatternsInfo(this AutomationElement element)
        {
            var patterns = new List<PatternInfo>();
            //try
            //{
            //    if (element.Patterns.Value.IsSupported)
            //    {
            //        patterns.Add(new PatternInfo
            //        {
            //            PatternName = "Value",
            //            Properties = new Dictionary<string, object>()
            //            {
            //                { "IsReadOnly", element.Patterns.Value.Pattern.IsReadOnly.ValueOrDefault },
            //                { "Value", element.Patterns.Value.Pattern.Value.ValueOrDefault }
            //            }
            //        });
            //    }
            //    if (element.Patterns.Window.IsSupported)
            //    {
            //        patterns.Add(new PatternInfo
            //        {
            //            PatternName = "Window",
            //            Properties = new Dictionary<string, object>()
            //            {
            //                { "IsModal", element.Patterns.Window.Pattern.IsModal.ValueOrDefault },
            //                { "IsTopmost", element.Patterns.Window.Pattern.IsTopmost.ValueOrDefault },
            //                { "WindowVisualState", element.Patterns.Window.Pattern.WindowVisualState.ValueOrDefault.ToString() }
            //            }
            //        });
            //    }
            //}
            //catch
            //{
            //    // Ignore pattern retrieval errors
            //}
            return patterns;
        }

        public static string GetIdentifier(this AutomationElement element)
        {
            
            var id = element.GetSafeAutomationID();
            if (!string.IsNullOrEmpty(id))
            {
                return $"ID: {id}";
            }
            var name = element.GetSafeName();
            if (!string.IsNullOrEmpty(name))
            {
                return $"Name: {name}";
            }
            var type = element.GetSafeControlType();
            if (!string.IsNullOrEmpty(type))
            {
                return $"Type: {type}";
            }

            return "Unknown";
        }
    }
}