using System.Collections.Generic;
using System.Drawing;

namespace Recorder.Models
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
}