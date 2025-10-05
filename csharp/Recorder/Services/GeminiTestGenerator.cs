using Microsoft.Extensions.Logging;
using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using GenerativeAI.Types;
using GenerativeAI.Tools;
using GenerativeAI;
using GenerativeAI.Clients;
using Newtonsoft.Json;

namespace Recorder.Services
{
    public class GeminiTestGenerator
    {
        private const string Model = "gemini-flash-latest";

        private readonly ILogger<GeminiTestGenerator> _logger;
        private readonly InputUiaService _inputUiaService;
        private readonly IAskHumanService _askHumanService;
        private GeminiTools _tools;
        private GenerativeModel _generativeModel;
        private FileClient _fileClient;
        private string _systemPrompt;

        public GeminiTestGenerator(ILogger<GeminiTestGenerator> logger, InputUiaService inputUiaService, IAskHumanService askHumanService, GeminiTools tools)
        {
            _logger = logger;
            _inputUiaService = inputUiaService;
            _askHumanService = askHumanService;
            _tools = tools;
        }

        private void InitializeClient()
        {
            _logger.LogInformation("Initializing Gemini client...");
            var apiKey = Environment.GetEnvironmentVariable("GEMINI_API_KEY");
            if (string.IsNullOrEmpty(apiKey))
            {
                var message = "GEMINI_API_KEY environment variable not set.";
                _logger.LogError(message);
                throw new InvalidOperationException(message);
            }
            var googleAI = new GoogleAi(apiKey, logger: _logger);
            _generativeModel = googleAI.CreateGenerativeModel(Model);
            _fileClient = googleAI.CreateGeminiModel(Model).Files;
            _logger.LogInformation("Gemini client initialized successfully.");

            

        }

        private void LoadSystemPrompt()
        {
            _logger.LogInformation("Loading system prompt...");
            string promptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "SystemPrompt.md");
            if (!File.Exists(promptPath))
            {
                var message = $"`SystemPrompt.md` not found at {promptPath}";
                _logger.LogError(message);
                throw new FileNotFoundException(message);
            }
            _systemPrompt = File.ReadAllText(promptPath);
            _logger.LogInformation("System prompt loaded successfully.");
        }

        public async Task GenerateAndRunTestAsync(string projectDir, string recordingDir, string processName, bool copyTemplate)
        {
            if (copyTemplate)
            {
                projectDir = CopyTemplateFiles(projectDir);
            }
            _logger.LogInformation("Starting test generation process...");
            InitializeClient();
            LoadSystemPrompt();

            _logger.LogInformation("Initializing Gemini tools...");
            _tools.ProjectDir = projectDir;
            _tools.ProcessName = processName;
            _tools.FileClient = _fileClient;

            var functionTool = _tools.AsGoogleFunctionTool();
            _generativeModel.AddFunctionTool(functionTool);
            _generativeModel.FunctionCallingBehaviour = new GenerativeAI.Core.FunctionCallingBehaviour
            {
                AutoCallFunction = true,
                //todo set reply to false to be able to upload files before replying
                AutoReplyFunction = true,
                AutoHandleBadFunctionCalls = true
            };
            _logger.LogInformation("Gemini tools initialized.");

            _logger.LogInformation("Starting chat session...");
            var chat = _generativeModel.StartChat(
                systemInstruction: _systemPrompt
            );

            var request = new GenerateContentRequest();

            await AddDirectoryFiles(recordingDir, request);
            var userPrompt = "Generate a C# UI test script using FlaUI and MSTest based on the recording. Follow the instructions in the system prompt to use the available tools.";
            request.AddText(userPrompt);
            _logger.LogInformation("Initial prompt: {userPrompt}", userPrompt);

            for (int i = 0; i < 10; i++)
            {
                _logger.LogInformation("Iteration {i}", i + 1);
                var response = await chat.GenerateContentAsync(request);

                var responseText = response.Text;
                _logger.LogInformation($"LLM->User: {responseText}");
                if (responseText.Contains("TEST_GENERATION_COMPLETE"))
                {
                    _logger.LogInformation("Test generation complete signal received.");
                    break;
                }


                request = new GenerateContentRequest();
                request.AddText("Please continue");
            }
        }

        private async Task AddDirectoryFiles(string directory, GenerateContentRequest req)
        {
            foreach (var filePath in Directory.EnumerateFiles(directory))
            {
                _logger.LogInformation("Adding file: {filePath}", filePath);
                var finalName = filePath;
                //rename json to json.txt to avoid upload issues
                if (finalName.EndsWith(".json", StringComparison.OrdinalIgnoreCase))
                {
                    finalName = finalName + ".txt";
                    File.Move(filePath, finalName);
                }
                var file = await _fileClient.UploadFileAsync(finalName);
                await _fileClient.AwaitForFileStateActiveAsync(file, 15, new CancellationToken());
                req.AddRemoteFile(file);
            }
        }

        private string CopyTemplateFiles(string templateDir)
        {
            if (!Directory.Exists(templateDir))
            {
                throw new InvalidDataException($"Template directory not found at {templateDir}");
            }

            var newDirName = $"{Path.GetFileName(templateDir)}_{DateTime.Now:yyyyMMdd_HHmmss}";
            var newDirPath = Path.Combine(Path.GetDirectoryName(templateDir), newDirName);

            Directory.CreateDirectory(newDirPath);


            foreach (var file in Directory.GetFiles(templateDir, "*", SearchOption.AllDirectories))
            {
                var relativePath = file.Substring(templateDir.Length + 1);
                var destFile = Path.Combine(newDirPath, relativePath);
                Directory.CreateDirectory(Path.GetDirectoryName(destFile));
                File.Copy(file, destFile, true);
            }
            _logger.LogInformation("Template files copied to {newDirPath}", newDirPath);
            return newDirPath;
        }
    }
}