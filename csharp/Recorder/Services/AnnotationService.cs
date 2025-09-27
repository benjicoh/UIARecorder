using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading.Tasks;

namespace Recorder.Services
{
    public class AnnotationService
    {
        private readonly List<Dictionary<string, object>> _annotations = new List<Dictionary<string, object>>();
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

        public void AddAnnotation(string eventType, object eventData, List<Dictionary<string, object>> elementHierarchy)
        {
            var timestamp = (DateTime.UtcNow - _startTime).TotalSeconds;
            var annotation = new Dictionary<string, object>
            {
                ["timestamp"] = timestamp,
                ["event_type"] = eventType,
                ["event_data"] = eventData,
                ["element_hierarchy"] = elementHierarchy
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