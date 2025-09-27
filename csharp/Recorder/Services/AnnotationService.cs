using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace Recorder.Services
{
    public enum EventType
    {
        MouseClick,
        KeyPress,
        Unknown
    }

    public class AnnotationInfo
    {
        public double Timestamp { get; set; }
        public string EventType { get; set; }
        public object EventData { get; set; }
        public ElementInfo ElementHierarchy { get; set; }
    }
    public class AnnotationService
    {
        private readonly List<AnnotationInfo> _annotations = new List<AnnotationInfo>();
        private readonly ILogger<AnnotationService> _logger;
        private DateTime _startTime;

        public AnnotationService(ILogger<AnnotationService> logger)
        {
            _logger = logger;
        }

        public void Start()
        {
            _startTime = DateTime.UtcNow;
            _annotations.Clear();
        }

        public void AddAnnotation(EventType eventType, object eventData, ElementInfo elementHierarchy)
        {
            var timestamp = (DateTime.UtcNow - _startTime).TotalSeconds;
            var annotation = new AnnotationInfo
            {
                Timestamp = timestamp,
                EventType = eventType.ToString(),
                EventData = eventData,
                ElementHierarchy = elementHierarchy
            };
            _annotations.Add(annotation);
        }

        public async Task StopAndSaveAsync(string filePath)
        {
            try
            {
                var json = JsonConvert.SerializeObject(_annotations, Formatting.Indented);
                await File.WriteAllTextAsync(filePath, json);
                _logger.LogInformation("Annotations saved to {FilePath}", filePath);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Failed to save annotations to file.");
            }
        }
    }
}