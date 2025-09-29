using System.Collections.Generic;

namespace Recorder.Models
{
    public class Configuration
    {
        public List<string> WhitelistedProcesses { get; set; } = new List<string>();
        public string ProjectDirectory { get; set; }
        public string RecordingsDirectory { get; set; }
    }
}