using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Agent.Models
{
    public class GenerateFromUserRecordingParams
    {
        [JsonPropertyName("recordingDir")]
        public string RecordingDir { get; set; }

        [JsonPropertyName("projectFiles")]
        public List<string> ProjectFiles { get; set; }

        [JsonPropertyName("additionalPrompt")]
        public string AdditionalPrompt { get; set; }

        [JsonPropertyName("outputDir")]
        public string OutputDir { get; set; }
    }

    public class RefineGenerationParams
    {
        [JsonPropertyName("lastRunOutputDir")]
        public string LastRunOutputDir { get; set; }

        [JsonPropertyName("projectFiles")]
        public List<string> ProjectFiles { get; set; }

        [JsonPropertyName("additionalPrompt")]
        public string AdditionalPrompt { get; set; }

        [JsonPropertyName("outputDir")]
        public string OutputDir { get; set; }
    }

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