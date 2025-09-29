using FlaUI.Core.Tools;
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;

namespace Recorder.Services
{
    public class GeminiTools : IGeminiTools
    {
        private readonly string _projectDir;
        private readonly string _processName;
        private readonly InputUiaService _inputUiaService;

        public GeminiTools(string projectDir, string processName,InputUiaService inputUiaService)
        {
            _projectDir = projectDir;
            _processName = processName;
            _inputUiaService = inputUiaService;
        }

        public Task<string> AddFile(string path, string newContent, System.Threading.CancellationToken cancellationToken = default)
        {
            var fullPath = Path.Combine(_projectDir, path);
            Directory.CreateDirectory(Path.GetDirectoryName(fullPath));
            File.WriteAllText(fullPath, newContent);
            return Task.FromResult($"File {path} added successfully.");
        }

        public async Task<string> Compile(CancellationToken cancellationToken = default)
        {
            var result = await RunCommandAsync("dotnet", "build", _projectDir);
            return $"Exit Code: {result.returnCode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}";
        }

        public Task<string> DeleteFile(string path, System.Threading.CancellationToken cancellationToken = default)
        {
            var fullPath = Path.Combine(_projectDir, path);
            if (File.Exists(fullPath))
            {
                File.Delete(fullPath);
                return Task.FromResult($"File {path} deleted successfully.");
            }
            return Task.FromResult($"File {path} not found.");
        }

        public async Task<string> DumpUi(CancellationToken cancellationToken = default)
        {
            var result = await _inputUiaService.DumpUiTreeAsync(_processName);
            return result;
        }

        public Task<string> ReadProject(CancellationToken cancellationToken = default)
        {
            var sb = new StringBuilder();
            var files = Directory.GetFiles(_projectDir, "*.*", SearchOption.AllDirectories);

            foreach (var file in files)
            {
                if (file.Contains("bin") || file.Contains("obj"))
                    continue;
                if (file.EndsWith(".cs") || file.EndsWith(".csproj"))
                {
                    var relativePath = Path.GetRelativePath(_projectDir, file);
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
            var fullPath = Path.Combine(_projectDir, path);
            if (File.Exists(fullPath))
            {
                File.WriteAllText(fullPath, newContent);
                return Task.FromResult($"File {path} replaced successfully.");
            }
            return Task.FromResult($"File {path} not found.");
        }

        public async Task<string> RunTest(bool record, CancellationToken cancellationToken = default)
        {
            // Recording functionality not implemented yet.
            var result = await RunCommandAsync("dotnet", "test --logger \"console;verbosity=detailed\"", _projectDir);
            return $"Exit Code: {result.returnCode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}";
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