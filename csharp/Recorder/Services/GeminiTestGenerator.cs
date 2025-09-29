using Google.GenerativeAI.GenerativeAI;
using Google.GenerativeAI.Chat;
using Microsoft.Extensions.Logging;
using System;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using GenerativeAI.Types;
using GenerativeAI.Tools;

namespace Recorder.Services
{
    public class GeminiTestGenerator
    {
        private const string RunOutputDirectory = "generated_scripts/{timestamp}";
        private const string Model = "gemini-1.5-flash-latest";

        private readonly ILogger<GeminiTestGenerator> _logger;
        private readonly InputUiaService _inputUiaService;
        private GenerativeModel _generativeModel;
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
            _generativeModel = googleAI.CreateGenerativeModel(model: Model);
        }

        private void LoadSystemPrompt()
        {
            string promptPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "flaui_prompt.md");
            if (!File.Exists(promptPath))
            {
                var message = $"`flaui_prompt.md` not found at {promptPath}";
                _logger.LogError(message);
                throw new FileNotFoundException(message);
            }
            _systemPrompt = File.ReadAllText(promptPath);
        }

        public async Task GenerateAndRunTestAsync(string templateProjectDir, string recordingDir, string processName, string windowTitle)
        {
            InitializeClient();
            LoadSystemPrompt();

            var runOutputRoot = RunOutputDirectory.Replace("{timestamp}", DateTime.Now.ToString("yyyyMMdd-HHmmss"));
            Directory.CreateDirectory(runOutputRoot);
            _logger.LogInformation("Run output directory: {runOutputRoot}", runOutputRoot);

            var projectDir = Path.Combine(runOutputRoot, Path.GetFileName(templateProjectDir));
            CopyDirectory(templateProjectDir, projectDir);
            _logger.LogInformation("Copied template project to {projectDir}", projectDir);

            var tools = new GeminiTools(projectDir, processName, windowTitle, _inputUiaService);
            var functionTool = tools.AsGoogleFunctionTool();
            _generativeModel.AddFunctionTool(functionTool);

            var chat = _generativeModel.StartChat(
                systemInstruction: _systemPrompt
            );

            var request = new GenerateContentRequest();
            AddDirectoryFiles(recordingDir, request);
            request.AddText("Generate a C# UI test script using FlaUI and MSTest based on the recording. Follow the instructions in the system prompt to use the available tools.");

            for (int i = 0; i < 20; i++)
            {
                var response = await chat.SendMessageAsync(request);
                var functionCalls = response.GetFunctionCalls().ToList();

                if (functionCalls.Any())
                {
                    _logger.LogInformation("LLM requested a tool call: {functionCall}", functionCalls.First().Name);
                    var toolResponse = await functionTool.ExecuteAsync(functionCalls.First());
                    request = new GenerateContentRequest { Contents = { toolResponse.ToContent() } };
                }
                else
                {
                    _logger.LogInformation("LLM finished with response: {text}", response.Text);
                    break;
                }
            }
        }

        private void AddDirectoryFiles(string directory, GenerateContentRequest req)
        {
            foreach (var filePath in Directory.EnumerateFiles(directory))
            {
                _logger.LogInformation("Adding file: {filePath}", filePath);
                req.AddInlineFile(filePath);
            }
        }

        private static void CopyDirectory(string sourceDir, string destinationDir)
        {
            Directory.CreateDirectory(destinationDir);
            foreach (var file in Directory.GetFiles(sourceDir, "*", SearchOption.AllDirectories))
            {
                string destFile = Path.Combine(destinationDir, Path.GetRelativePath(sourceDir, file));
                Directory.CreateDirectory(Path.GetDirectoryName(destFile));
                File.Copy(file, destFile, true);
            }
        }
    }
}