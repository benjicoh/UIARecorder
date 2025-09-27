using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using Recorder.Models;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace Recorder.Services
{
    public class AnnotationService
    {
        private readonly List<ElementInfo> _knownElements = new List<ElementInfo>();
        private readonly ILogger<AnnotationService> _logger;
        private readonly object _lock = new object();
        private DateTime _startTime;

        public AnnotationService(ILogger<AnnotationService> logger)
        {
            _logger = logger;
        }

        public void Start()
        {
            _startTime = DateTime.UtcNow;
            lock (_lock)
            {
                _knownElements.Clear();
            }
        }

        public void AddEvent(ElementInfo elementHierarchy, string eventType, object eventData)
        {
            var timestamp = (DateTime.UtcNow - _startTime).TotalSeconds;
            var newEvent = new AnnotationEvent
            {
                Timestamp = timestamp,
                EventType = eventType,
                EventData = eventData
            };

            if (elementHierarchy != null)
            {
                lock (_lock)
                {
                    MergeHierarchy(_knownElements, elementHierarchy, newEvent);
                }
            }
        }

        private void MergeHierarchy(List<ElementInfo> existingChildren, ElementInfo newElement, AnnotationEvent newEvent)
        {
            var existingElement = existingChildren.FirstOrDefault(e => e.GetUniqueKey() == newElement.GetUniqueKey());

            if (existingElement == null)
            {
                existingChildren.Add(newElement);
                var leaf = newElement;
                while (leaf.Children.Any())
                {
                    leaf = leaf.Children.First();
                }
                leaf.Events.Add(newEvent);
            }
            else
            {
                if (newElement.Children.Any())
                {
                    MergeHierarchy(existingElement.Children, newElement.Children.First(), newEvent);
                }
                else
                {
                    existingElement.Events.Add(newEvent);
                }
            }
        }

        public async Task StopAndSaveAsync(string filePath)
        {
            try
            {
                string json;
                lock (_lock)
                {
                    json = JsonConvert.SerializeObject(_knownElements, Formatting.Indented);
                }
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