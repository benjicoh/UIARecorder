using Microsoft.Extensions.Logging;
using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using GenerativeAI.Types;
using GenerativeAI.Tools;
using GenerativeAI;
using GenerativeAI.Clients;

namespace Recorder.Services
{
    public class GeminiTestGenerator
    {
        private const string RunOutputDirectory = "generated_scripts/{timestamp}";
        private const string Model = "gemini-flash-latest";

        private readonly ILogger<GeminiTestGenerator> _logger;
        private readonly InputUiaService _inputUiaService;
        private GenerativeModel _generativeModel;
        private FileClient _fileClient;
        private string _systemPrompt;

        public GeminiTestGenerator(ILogger<GeminiTestGenerator> logger, InputUiaService inputUiaService)
        {
            _logger = logger;
            _inputUiaService = inputUiaService;
            
        }

        private void InitializeClient()
        {
            var apiKey = Environment.GetEnvironmentVariable("GEMINI_API_KEY");
            if (string.IsNullOrEmpty(apiKey))
            {
                var message = "GEMINI_API_KEY environment variable not set.";
                _logger.LogError(message);
                throw new InvalidOperationException(message);
            }
            var googleAI = new GoogleAi(apiKey);
            _generativeModel = googleAI.CreateGenerativeModel(Model);
            _fileClient = googleAI.CreateGeminiModel(Model).Files;
        }

        private void LoadSystemPrompt()
        {
            string promptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "SystemPrompt.md");
            if (!File.Exists(promptPath))
            {
                var message = $"`SystemPrompt.md` not found at {promptPath}";
                _logger.LogError(message);
                throw new FileNotFoundException(message);
            }
            _systemPrompt = File.ReadAllText(promptPath);
        }

        public async Task GenerateAndRunTestAsync(string projectDir, string recordingDir, string processName)
        {
            InitializeClient();
            LoadSystemPrompt();

            var runOutputRoot = RunOutputDirectory.Replace("{timestamp}", DateTime.Now.ToString("yyyyMMdd-HHmmss"));
            Directory.CreateDirectory(runOutputRoot);
            _logger.LogInformation("Run output directory: {runOutputRoot}", runOutputRoot);

            var tools = new GeminiTools(projectDir, processName, _inputUiaService);
            var functionTool = tools.AsGoogleFunctionTool();
            _generativeModel.AddFunctionTool(functionTool);
            _generativeModel.FunctionCallingBehaviour = new GenerativeAI.Core.FunctionCallingBehaviour
            {
                AutoCallFunction = true,
                AutoReplyFunction = true,
                AutoHandleBadFunctionCalls = true
            };

            var chat = _generativeModel.StartChat(
                systemInstruction: _systemPrompt
            );

            var request = new GenerateContentRequest();
            await AddDirectoryFiles(recordingDir, request);
            request.AddText("Generate a C# UI test script using FlaUI and MSTest based on the recording. Follow the instructions in the system prompt to use the available tools.");

            for (int i = 0; i < 20; i++)
            {
                var response = await chat.GenerateContentAsync(request);
                //log response.Text and any function calls
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
                req.AddRemoteFile(file);
            }
        }

    }
}