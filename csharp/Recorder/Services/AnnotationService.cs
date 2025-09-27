using Microsoft.Extensions.Logging;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;

namespace Recorder.Services
{
    public enum EventType
    {
        MouseClick,
        KeyPress,
        Unknown
    }

    public class AnnotationService
    {
        private readonly List<ElementInfo> _knownElements = new List<ElementInfo>();
        private readonly ILogger<AnnotationService> _logger;
        private DateTime _startTime;

        public AnnotationService(ILogger<AnnotationService> logger)
        {
            _logger = logger;
        }

        public void Start()
        {
            _startTime = DateTime.UtcNow;
            _knownElements.Clear();
        }

        public void AddAnnotation(EventType eventType, object eventData, ElementInfo elementHierarchy)
        {
            var timestamp = (DateTime.UtcNow - _startTime).TotalSeconds;
            var newEvent = new AnnotationEvent
            {
                Timestamp = timestamp,
                EventType = eventType.ToString(),
                EventData = eventData
            };

            if (elementHierarchy != null)
            {
                MergeHierarchy(_knownElements, elementHierarchy, newEvent);
            }
        }

        private void MergeHierarchy(List<ElementInfo> existingChildren, ElementInfo newElement, AnnotationEvent newEvent)
        {
            var existingElement = existingChildren.FirstOrDefault(e => e.GetUniqueKey() == newElement.GetUniqueKey());

            if (existingElement == null)
            {
                existingChildren.Add(newElement);
                // Since it's a new element, the event belongs to the leaf of this hierarchy
                var leaf = newElement;
                while (leaf.Children.Any())
                {
                    leaf = leaf.Children.First();
                }
                leaf.Events.Add(newEvent);
            }
            else
            {
                // If there are more children in the new hierarchy, recurse
                if (newElement.Children.Any())
                {
                    MergeHierarchy(existingElement.Children, newElement.Children.First(), newEvent);
                }
                else
                {
                    // This is the target element, add the event here
                    existingElement.Events.Add(newEvent);
                }
            }
        }

        public async Task StopAndSaveAsync(string filePath)
        {
            try
            {
                var json = JsonConvert.SerializeObject(_knownElements, Formatting.Indented);
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