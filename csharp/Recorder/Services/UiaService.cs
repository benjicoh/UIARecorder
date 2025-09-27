using FlaUI.Core;
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using System;
using System.Collections.Generic;
using System.Drawing;

namespace Recorder.Services
{

    public class AnnotationEvent
    {
        public double Timestamp { get; set; }
        public string EventType { get; set; }
        public object EventData { get; set; }
    }

    public class ElementInfo
    {
        public string AutomationID { get; set; }
        public string Name { get; set; }
        public string ControlType { get; set; }
        public Rectangle BoundingRectangle { get; set; }
        public List<PatternInfo> Patterns { get; set; } = new List<PatternInfo>();
        public List<ElementInfo> Children { get; set; } = new List<ElementInfo>();
        public List<AnnotationEvent> Events { get; set; } = new List<AnnotationEvent>();

        public string GetIdentifier()
        {
            if (!string.IsNullOrEmpty(AutomationID)) return $"ID: {AutomationID}";
            if (!string.IsNullOrEmpty(Name)) return $"Name: {Name}";
            if (!string.IsNullOrEmpty(ControlType)) return $"Type: {ControlType}";
            return "Unknown";
        }

        public string GetUniqueKey()
        {
            return $"{ControlType}-{Name}-{AutomationID}";
        }
    }

    public class PatternInfo
    {
        public string PatternName { get; set; }
        public Dictionary<string, object> Properties { get; set; } = new Dictionary<string, object>();
    }

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
            return _automation.FocusedElement();
        }

        public ElementInfo GetElementHierarchy(AutomationElement element)
        {
            if (element == null)
            {
                return null;
            }

            // First, build the chain up to the root
            var hierarchy = new List<AutomationElement>();
            while (element != null)
            {
                hierarchy.Add(element);
                element = element.Parent;
            }
            hierarchy.Reverse(); // Reverse to have root at the beginning

            // Now, build the ElementInfo tree from the root down
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
    }

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

        //also for name, control type , bounding rectangle
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

        #region Patterns
        public static List<PatternInfo> GetPatternsInfo(this AutomationElement element)
        {
            var patterns = new List<PatternInfo>();
            try
            {

                //if (element.Patterns.Selection.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Selection",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "CanSelectMultiple", element.Patterns.Selection.Pattern.CanSelectMultiple.ValueOrDefault },
                //            { "IsSelectionRequired", element.Patterns.Selection.Pattern.IsSelectionRequired.ValueOrDefault }
                //        }
                //    });
                //}
                if (element.Patterns.Value.PatternOrDefault != null)
                {
                    patterns.Add(new PatternInfo
                    {
                        PatternName = "Value",
                        Properties = new Dictionary<string, object>()
                        {
                            { "IsReadOnly", element.Patterns.Value.Pattern.IsReadOnly.ValueOrDefault },
                            { "Value", element.Patterns.Value.Pattern.Value.ValueOrDefault }
                        }
                    });
                }
                //if (element.Patterns.Invoke.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo { PatternName = "Invoke" });
                //}
                //if (element.Patterns.ExpandCollapse.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "ExpandCollapse",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "ExpandCollapseState", element.Patterns.ExpandCollapse.Pattern.ExpandCollapseState.ValueOrDefault.ToString() }
                //        }
                //    });
                //}
                //if (element.Patterns.Toggle.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Toggle",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "ToggleState", element.Patterns.Toggle.Pattern.ToggleState.ValueOrDefault.ToString() }
                //        }
                //    });
                //}
                //if (element.Patterns.Scroll.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Scroll",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "HorizontallyScrollable", element.Patterns.Scroll.Pattern.HorizontallyScrollable },
                //            { "VerticallyScrollable", element.Patterns.Scroll.Pattern.VerticallyScrollable },
                //            { "VerticalScrollPercent", element.Patterns.Scroll.Pattern.VerticalScrollPercent },
                //            { "HorizontalScrollPercent", element.Patterns.Scroll.Pattern.HorizontalScrollPercent }
                //        }
                //    });
                //}
                //if (element.Patterns.Grid.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Grid",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "RowCount", element.Patterns.Grid.Pattern.RowCount },
                //            { "ColumnCount", element.Patterns.Grid.Pattern.ColumnCount }
                //        }
                //    });
                //}
                //if (element.Patterns.Table.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Table",
                //    });
                //}

                //if (element.Patterns.Text.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Text",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "DocumentRange", element.Patterns.Text.Pattern.DocumentRange?.GetText(-1) ?? string.Empty },
                //            { "SupportedTextSelection", element.Patterns.Text.Pattern.SupportedTextSelection.ToString() }
                //        }
                //    });
                //}
                //if (element.Patterns.LegacyIAccessible.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "LegacyIAccessible",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "Name", element.Patterns.LegacyIAccessible.Pattern.Name },
                //            { "Value", element.Patterns.LegacyIAccessible.Pattern.Value },
                //            { "Description", element.Patterns.LegacyIAccessible.Pattern.Description },
                //            { "Role", element.Patterns.LegacyIAccessible.Pattern.Role },
                //            { "State", element.Patterns.LegacyIAccessible.Pattern.State }
                //        }
                //    });
                //}
                //if (element.Patterns.ScrollItem.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo { PatternName = "ScrollItem" });
                //}
                //if (element.Patterns.SelectionItem.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "SelectionItem",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "IsSelected", element.Patterns.SelectionItem.Pattern.IsSelected }
                //        }
                //    });
                //}
                //if (element.Patterns.TableItem.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "TableItem"
                //    });
                //}
                if (element.Patterns.Window.PatternOrDefault != null)
                {
                    patterns.Add(new PatternInfo
                    {
                        PatternName = "Window",
                        Properties = new Dictionary<string, object>()
                        {
                            { "IsModal", element.Patterns.Window.Pattern.IsModal.ValueOrDefault },
                            { "IsTopmost", element.Patterns.Window.Pattern.IsTopmost.ValueOrDefault },
                            { "WindowVisualState", element.Patterns.Window.Pattern.WindowVisualState.ValueOrDefault.ToString() }
                        }
                    });
                }
                //if (element.Patterns.Dock.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Dock",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "DockPosition", element.Patterns.Dock.Pattern.DockPosition.ToString() }
                //        }
                //    });
                //}
                //if (element.Patterns.MultipleView.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "MultipleView",
                //        Properties = new Dictionary<string, object>()
                //        {
                //            { "CurrentView", element.Patterns.MultipleView.Pattern.CurrentView },
                //            { "SupportedViews", string.Join(", ", element.Patterns.MultipleView.Pattern.SupportedViews) }
                //        }
                //    });
                //}
                //if (element.Patterns.Spreadsheet.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "Spreadsheet",
                //    });
                //}
                //if (element.Patterns.SpreadsheetItem.PatternOrDefault != null)
                //{
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "SpreadsheetItem",
                //    });
                //}
                //if (element.Patterns.TextEdit.PatternOrDefault != null)
                //{
                //    var pattern = element.Patterns.TextEdit.Pattern;
                //    patterns.Add(new PatternInfo
                //    {
                //        PatternName = "TextEdit"

                //    });
                //}

            }
            catch
            {
                // Ignore pattern retrieval errors
            }
            return patterns;
        }
        #endregion
    }
}