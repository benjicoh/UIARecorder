using Google.GenerativeAI.GenerativeAI;
using Google.GenerativeAI.Chat;
using Microsoft.Extensions.Logging;
using Recorder.Models;
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using GenerativeAI;
using GenerativeAI.Types;

namespace Recorder.Services
{
    public class GeminiTestGenerator
    {
        private const int MaxCompilationAttempts = 6;
        private const int MaxExecutionAttempts = 6;
        private const string RunOutputDirectory = "generated_scripts/{timestamp}";
        private const string CompilationIterationDir = "{run_output_dir}/compilation/iteration{i}";
        private const string ExecutionIterationDir = "{run_output_dir}/execution/iteration{i}";
        private const string Model = "gemini-2.5-flash-latest";

        private readonly ILogger<GeminiTestGenerator> _logger;
        private readonly InputUiaService _inputUiaService;
        private GenerativeModel _generativeModel;
        private ChatSession _chat;
        private GenerateContentRequest _request;
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
            _request = new GenerateContentRequest();
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

            _generativeModel.UseJsonMode = true;
            _chat = _generativeModel.StartChat(
                systemInstruction: _systemPrompt
            );

            var runOutputRoot = RunOutputDirectory.Replace("{timestamp}", DateTime.Now.ToString("yyyyMMdd-HHmmss"));
            Directory.CreateDirectory(runOutputRoot);
            _logger.LogInformation("Run output directory: {runOutputRoot}", runOutputRoot);

            var projectDir = Path.Combine(runOutputRoot, Path.GetFileName(templateProjectDir));
            CopyDirectory(templateProjectDir, projectDir);
            _logger.LogInformation("Copied template project to {projectDir}", projectDir);

            string flauiProjectPath = Path.Combine(projectDir, $"{Path.GetFileName(templateProjectDir)}.csproj");

            _logger.LogInformation("Analyzing data in: {recordingDir}", recordingDir);
            AddDirectoryFiles(recordingDir, _request);
            AddProjectFiles(projectDir, _request);
            _request.AddText("Generate the initial C# script to perform the recorded scenario using FlaUI and MSTest.");

            // --- Compilation Loop ---
            bool compilationSuccess = false;
            CodeResponse codeResponse = null;
            string iterationDir = "";

            for (int i = 0; i < MaxCompilationAttempts; i++)
            {
                _logger.LogInformation("--- Compilation Attempt {i}/{MaxCompilationAttempts} ---", i + 1, MaxCompilationAttempts);

                if (i > 0)
                {
                    _request.AddText("The previously generated script failed to compile.\nAttached are the compilation logs for analysis and script refinement.")
                }

                codeResponse = await _chat.GenerateObjectAsync<CodeResponse>(_request);

                if (!string.IsNullOrEmpty(codeResponse.FailureReason))
                    _logger.LogInformation("LLM failure reason: {failureReason}", codeResponse.FailureReason);
                if (!string.IsNullOrEmpty(codeResponse.Comments))
                    _logger.LogInformation("LLM comments: {comments}", codeResponse.Comments);

                iterationDir = CompilationIterationDir.Replace("{run_output_dir}", runOutputRoot).Replace("{i}", i.ToString());
                Directory.CreateDirectory(iterationDir);
                WriteResponseFiles(codeResponse, projectDir);
                WriteResponseFiles(codeResponse, iterationDir, renameToTxt: true);

                _logger.LogInformation("Compiling scripts: {flauiProjectPath}", flauiProjectPath);
                var compilationResult = await RunCommandAsync("dotnet", "build", projectDir);
                _logger.LogInformation("--- Compilation Output ---\n{stdout}\n{stderr}\n---", compilationResult.stdout, compilationResult.stderr);

                string logPath = Path.Combine(iterationDir, "compilation_log.txt");
                string logOutput = $"STDOUT:\n{compilationResult.stdout}\n\nSTDERR:\n{compilationResult.stderr}";
                await File.WriteAllTextAsync(logPath, logOutput);
                _logger.LogInformation("Compilation log file written to {logPath}", logPath);

                if (compilationResult.returnCode == 0)
                {
                    _logger.LogInformation("--- Compilation Successful! ---");
                    compilationSuccess = true;
                    break;
                }

                _logger.LogWarning("--- Compilation Failed! ---");
                _request = new GenerateContentRequest();
                _request.AddText($"STDOUT : {compilationResult.stdout}");
                _request.AddText($"STDERR : {compilationResult.stderr}");
                if (i == MaxCompilationAttempts - 1) break;
            }

            if (!compilationSuccess)
            {
                _logger.LogError("--- Max Compilation Retries Reached! Could not compile the script. ---");
                return;
            }

            // --- Execution Loop ---
            bool executionSuccess = false;
            for (int i = 0; i < MaxExecutionAttempts; i++)
            {
                _logger.LogInformation("--- Execution Attempt {i}/{MaxExecutionAttempts} ---", i + 1, MaxExecutionAttempts);
                iterationDir = ExecutionIterationDir.Replace("{run_output_dir}", runOutputRoot).Replace("{i}", (i + MaxCompilationAttempts).ToString());
                Directory.CreateDirectory(iterationDir);

                _logger.LogInformation("Running test: {flauiProjectPath}", flauiProjectPath);
                var executionResult = await RunCommandAsync("dotnet", "test --logger \"console;verbosity=detailed\"", projectDir);
                _logger.LogInformation("--- Execution Output ---\n{stdout}\n{stderr}\n---", executionResult.stdout, executionResult.stderr);

                string logPath = Path.Combine(iterationDir, "execution_log.txt");
                string logOutput = $"STDOUT:\n{executionResult.stdout}\n\nSTDERR:\n{executionResult.stderr}";
                await File.WriteAllTextAsync(logPath, logOutput);
                _logger.LogInformation("Execution log file written to {logPath}", logPath);

                if (executionResult.stdout.Contains("Passed!"))
                {
                    _logger.LogInformation("--- Test Executed Successfully! ---");
                    executionSuccess = true;
                    break;
                }

                _logger.LogWarning("--- Test Execution Failed! ---");
                if (i == MaxExecutionAttempts - 1) break;

                _logger.LogInformation("Collecting and sending data for refinement...");
                string uiDumpPath = Path.Combine(iterationDir, "ui_dump.json.txt");
                var res = await _inputUiaService.DumpUiTreeAsync(processName, windowTitle, uiDumpPath);
                _logger.LogInformation("UI tree dump result: {res}", res);
                _request = new GenerateContentRequest();
                _request.AddText"The previously generated script failed to execute correctly.\nAttached are the logs of the failed run for analysis, and script refinement.")
                };
                errorPromptParts.AddRange(await PrepareFileParts(iterationDir));

                codeResponse = await _chat.GenerateObjectAsync<CodeResponse>(errorPromptParts);

                if (!string.IsNullOrEmpty(codeResponse.FailureReason))
                    _logger.LogInformation("LLM failure reason: {failureReason}", codeResponse.FailureReason);
                if (!string.IsNullOrEmpty(codeResponse.Comments))
                    _logger.LogInformation("LLM comments: {comments}", codeResponse.Comments);

                WriteResponseFiles(codeResponse, projectDir);
                WriteResponseFiles(codeResponse, iterationDir, renameToTxt: true);
            }
            if (!executionSuccess)
            {
                _logger.LogError("--- Max Execution Retries Reached! Could not fix the script. ---");
            }
        }

        private void AddDirectoryFiles(string directory, GenerateContentRequest req)
        {

            foreach (var filePath in Directory.EnumerateFiles(directory))
            {
                _logger.LogInformation($"Adding file: {filePath}");
                req.AddInlineFile(filePath);

            }
        }

        private void AddProjectFiles(string sourceDir, GenerateContentRequest req)
        {
            foreach (var file in Directory.GetFiles(sourceDir, "*.*", SearchOption.AllDirectories))
            {
                var dirPath = Path.GetDirectoryName(file);
                if (dirPath.EndsWith("bin") || dirPath.EndsWith("obj"))
                {
                    continue;
                }

                if (file.EndsWith(".cs") || file.EndsWith(".csproj"))
                {
                    req.AddInlineFile(file);
                }
            }
        }

        private void WriteResponseFiles(CodeResponse response, string targetDir, bool renameToTxt = false)
        {
            Directory.CreateDirectory(targetDir);
            string testClassPath = Path.Combine(targetDir, "TestClass.cs");
            string appPagePath = Path.Combine(targetDir, "ApplicationPage.cs");

            File.WriteAllLines(testClassPath, response.TestCaseCodeLines);
            File.WriteAllLines(appPagePath, response.ApplicationPageCodeLines);

            if (renameToTxt)
            {
                File.Move(testClassPath, testClassPath + ".txt");
                File.Move(appPagePath, appPagePath + ".txt");
            }
        }

        private async Task<(int returnCode, string stdout, string stderr)> RunCommandAsync(string command, string args, string workingDirectory)
        {
            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = command,
                    Arguments = args,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    WorkingDirectory = workingDirectory
                }
            };

            var stdOutBuilder = new StringBuilder();
            var stdErrBuilder = new StringBuilder();

            process.OutputDataReceived += (sender, eventArgs) => { if(eventArgs.Data != null) stdOutBuilder.AppendLine(eventArgs.Data); };
            process.ErrorDataReceived += (sender, eventArgs) => { if(eventArgs.Data != null) stdErrBuilder.AppendLine(eventArgs.Data); };

            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            await process.WaitForExitAsync();

            return (process.ExitCode, stdOutBuilder.ToString(), stdErrBuilder.ToString());
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