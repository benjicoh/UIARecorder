using FlaUI.Core.Tools;
using GenerativeAI.Clients;
using Microsoft.Extensions.Logging;
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;

namespace Recorder.Services
{
    public class GeminiTools : IGeminiTools
    {
        private readonly InputUiaService _inputUiaService;
        private readonly ILogger<GeminiTools> _logger;
        private readonly IAskHumanService _askHumanService;

        public string ProjectDir { get; set; }
        public string ProcessName { get; set; }

        public FileClient FileClient { get; set; }


        public GeminiTools(InputUiaService inputUiaService, ILogger<GeminiTools> logger, IAskHumanService askHumanService)
        {
            _inputUiaService = inputUiaService;
            _logger = logger;
            _askHumanService = askHumanService;
        }

        public Task<string> AddFile(string path, string newContent, System.Threading.CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Adding file {path}...");
            var fullPath = Path.Combine(ProjectDir, path);
            Directory.CreateDirectory(Path.GetDirectoryName(fullPath));
            File.WriteAllText(fullPath, newContent);
            return Task.FromResult($"File {path} added successfully.");
        }

        public async Task<string> Compile(CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Compiling project...");
            var result = await RunCommandAsync("dotnet", "build", ProjectDir);
            _logger.LogInformation($"Compilation finished\n{result.stdout}");
            return $"Exit Code: {result.returnCode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}";
        }

        public Task<string> DeleteFile(string path, System.Threading.CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Deleting file {path}...");
            var fullPath = Path.Combine(ProjectDir, path);
            if (File.Exists(fullPath))
            {
                File.Delete(fullPath);
                return Task.FromResult($"File {path} deleted successfully.");
            }
            return Task.FromResult($"File {path} not found.");
        }

        public async Task<string> DumpUiAutomationTree(CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Dumping UI for process {ProcessName}...");
            var result = await _inputUiaService.DumpUiTreeAsync(ProcessName);
            return result;
        }

        public Task<string> ReadProject(CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Reading project from {ProjectDir}...");
            var sb = new StringBuilder();
            var files = Directory.GetFiles(ProjectDir, "*.*", SearchOption.AllDirectories);

            foreach (var file in files)
            {
                if (file.Contains("bin") || file.Contains("obj"))
                    continue;
                if (file.EndsWith(".cs") || file.EndsWith(".csproj"))
                {
                    var relativePath = Path.GetRelativePath(ProjectDir, file);
                    sb.AppendLine($"## `{relativePath}`");
                    sb.AppendLine("```csharp");
                    sb.AppendLine(File.ReadAllText(file));
                    sb.AppendLine("```");
                    sb.AppendLine();
                }
            }
            return Task.FromResult(sb.ToString());
        }

        public Task<string> ReplaceFile(string path, string newContent, System.Threading.CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Replacing file {path}...");
            var fullPath = Path.Combine(ProjectDir, path);
            if (File.Exists(fullPath))
            {
                File.WriteAllText(fullPath, newContent);
                return Task.FromResult($"File {path} replaced successfully.");
            }
            return Task.FromResult($"File {path} not found.");
        }

        public async Task<string> RunTest(CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Running tests...");
            var result = await RunCommandAsync("dotnet", "test --logger \"console;verbosity=detailed\"", ProjectDir);
            _logger.LogInformation($"Test run finished\n{result.stdout}");
            return $"Exit Code: {result.returnCode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}";
        }

        public async Task<string> RunCommandLine(string cmd, string args, CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Running cmd {cmd}...");
            var result = await RunCommandAsync(cmd, args, ProjectDir);
            _logger.LogInformation($"Command finished\n{result.stdout}");
            return $"Exit Code: {result.returnCode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}";
        }

        public async Task<string> LogThought(string thought, CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Thought: {thought}");
            await Task.CompletedTask;
            return "Thought logged.";
        }
        public Task<string> AskHuman(string question, System.Threading.CancellationToken cancellationToken = default)
        {
            _logger.LogInformation($"Asking human: {question}");
            var answer = _askHumanService.Ask(question);
            _logger.LogInformation($"Human responded: {answer}");
            return Task.FromResult(answer);
        }

        public async Task<string> TakeScreenshot(CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Taking screenshot...");
            var screenshotPath = Path.Combine(ProjectDir, "screenshot.png");
            _inputUiaService.TakeScreenshot(screenshotPath);
            //upload the file back
            var file = await FileClient.UploadFileAsync(screenshotPath);
            await FileClient.AwaitForFileStateActiveAsync(file, 15, new CancellationToken());
            _logger.LogInformation($"Screenshot saved to {screenshotPath}");
            return $"Screenshot saved to {screenshotPath}";
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
    }
}