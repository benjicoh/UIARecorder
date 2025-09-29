using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Recorder.Models
{
    public class CodeResponse
    {
        [JsonPropertyName("testcase_code_lines")]
        public List<string> TestCaseCodeLines { get; set; }

        [JsonPropertyName("application_page_code_lines")]
        public List<string> ApplicationPageCodeLines { get; set; }

        [JsonPropertyName("failure_reason")]
        public string FailureReason { get; set; }

        [JsonPropertyName("comments")]
        public string Comments { get; set; }
    }
}