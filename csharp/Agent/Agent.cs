using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;
using Agent.Models;
using Google.Ai.Generativelanguage.V1Beta;
using Google.Protobuf;
using ModelContextProtocol.CSharp.SDK;
using ModelContextProtocol.CSharp.SDK.Tools;

namespace Agent
{
    public class Agent
    {
        private readonly GenerativeLanguageServiceClient _geminiClient;
        private readonly ModelContext _mcp;
        private readonly string _systemPrompt;
        private Content _chatHistory;

        public Agent()
        {
            var apiKey = Environment.GetEnvironmentVariable("GEMINI_API_KEY");
            if (string.IsNullOrEmpty(apiKey))
            {
                throw new InvalidOperationException("GEMINI_API_KEY environment variable not set.");
            }
            _geminiClient = new GenerativeLanguageServiceClientBuilder { ApiKey = apiKey }.Build();
            _mcp = new ModelContext();

            var assembly = Assembly.GetExecutingAssembly();
            var resourceName = "Agent.flaui_prompt.md";
            using (var stream = assembly.GetManifestResourceStream(resourceName))
            {
                if (stream == null)
                {
                    throw new FileNotFoundException($"Could not find embedded resource: {resourceName}");
                }
                using (var reader = new StreamReader(stream))
                {
                    _systemPrompt = reader.ReadToEnd();
                }
            }

            SetupTools();
        }

        private void SetupTools()
        {
            _mcp.RegisterTool(new Tool<GenerateFromUserRecordingParams, string>
            {
                Name = "GenerateFromUserRecording",
                Description = "Generates C# automation code from a user recording.",
                Execute = async (parameters) => await GenerateFromUserRecording(parameters)
            });

            _mcp.RegisterTool(new Tool<RefineGenerationParams, string>
            {
                Name = "RefineGeneration",
                Description = "Refines previously generated code based on feedback.",
                Execute = async (parameters) => await RefineGeneration(parameters)
            });
        }

        private async Task<IEnumerable<Part>> UploadDirectoryFiles(string directory)
        {
            var parts = new List<Part>();
            foreach (var filePath in Directory.GetFiles(directory, "*.*", SearchOption.AllDirectories))
            {
                var response = await _geminiClient.UploadFileAsync(new UploadFileRequest
                {
                    File = new File
                    {
                        DisplayName = Path.GetFileName(filePath),
                        MimeType = "application/octet-stream",
                        Content = ByteString.FromStream(File.OpenRead(filePath))
                    }
                });
                parts.Add(new Part { FileData = new FileData { MimeType = response.File.MimeType, FileUri = response.File.Uri } });
            }
            return parts;
        }

        private async Task<string> GenerateCode(List<Part> promptParts, string outputDir, string modelName = "models/gemini-flash-latest")
        {
            try
            {
                var request = new GenerateContentRequest
                {
                    Model = modelName,
                    GenerationConfig = new GenerationConfig
                    {
                        ResponseMimeType = "application/json"
                    },
                    SystemInstruction = new Content { Parts = { new Part { Text = _systemPrompt } } }
                };

                if (_chatHistory != null)
                {
                    request.Contents.Add(_chatHistory);
                }
                request.Contents.Add(new Content { Role = "user", Parts = { promptParts } });

                var response = await _geminiClient.GenerateContentAsync(request);

                if (response.Candidates == null || !response.Candidates.Any())
                {
                    return "Error: Received no response from the model.";
                }

                var jsonResponse = response.Candidates.First().Content.Parts.First().Text;
                var codeResponse = JsonSerializer.Deserialize<CodeResponse>(jsonResponse);

                if (codeResponse == null)
                {
                    return "Error: Failed to deserialize the model's response.";
                }

                _chatHistory = new Content { Role = "model", Parts = { new Part { Text = jsonResponse } } };

                Directory.CreateDirectory(outputDir);
                File.WriteAllText(Path.Combine(outputDir, "TestClass.cs"), string.Join("\n", codeResponse.TestCaseCodeLines ?? new List<string>()));
                File.WriteAllText(Path.Combine(outputDir, "ApplicationPage.cs"), string.Join("\n", codeResponse.ApplicationPageCodeLines ?? new List<string>()));

                return $"Code generated and saved to {outputDir}.";
            }
            catch (Exception ex)
            {
                return $"An error occurred during code generation: {ex.Message}";
            }
        }

        public async Task<string> GenerateFromUserRecording(GenerateFromUserRecordingParams parameters)
        {
            _chatHistory = null; // Reset chat history

            var promptParts = new List<Part>
            {
                new Part { Text = "Generate the initial C# script to perform the recorded scenario using FlaUI and MSTest." }
            };
            if (!string.IsNullOrEmpty(parameters.AdditionalPrompt))
            {
                promptParts.Add(new Part { Text = parameters.AdditionalPrompt });
            }

            var recordingFiles = await UploadDirectoryFiles(parameters.RecordingDir);
            promptParts.AddRange(recordingFiles);

            foreach(var projectFile in parameters.ProjectFiles)
            {
                 var response = await _geminiClient.UploadFileAsync(new UploadFileRequest
                {
                    File = new File
                    {
                        DisplayName = Path.GetFileName(projectFile),
                        MimeType = "application/octet-stream",
                        Content = ByteString.FromStream(File.OpenRead(projectFile))
                    }
                });
                promptParts.Add(new Part { FileData = new FileData { MimeType = response.File.MimeType, FileUri = response.File.Uri } });
            }

            return await GenerateCode(promptParts, parameters.OutputDir);
        }

        public async Task<string> RefineGeneration(RefineGenerationParams parameters)
        {
            if (_chatHistory == null)
            {
                return "Error: A generation must be started with GenerateFromUserRecording before refinement can occur.";
            }

            var promptParts = new List<Part>
            {
                new Part { Text = "The previously generated script failed to compile or run. Attached are the logs for analysis and script refinement." }
            };
             if (!string.IsNullOrEmpty(parameters.AdditionalPrompt))
            {
                promptParts.Add(new Part { Text = parameters.AdditionalPrompt });
            }

            var lastRunFiles = await UploadDirectoryFiles(parameters.LastRunOutputDir);
            promptParts.AddRange(lastRunFiles);

             foreach(var projectFile in parameters.ProjectFiles)
            {
                 var response = await _geminiClient.UploadFileAsync(new UploadFileRequest
                {
                    File = new File
                    {
                        DisplayName = Path.GetFileName(projectFile),
                        MimeType = "application/octet-stream",
                        Content = ByteString.FromStream(File.OpenRead(projectFile))
                    }
                });
                promptParts.Add(new Part { FileData = new FileData { MimeType = response.File.MimeType, FileUri = response.File.Uri } });
            }

            return await GenerateCode(promptParts, parameters.OutputDir);
        }

        public async Task StartAgent()
        {
            await _mcp.StartAsync();
        }
    }
}