using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading.Tasks;

namespace Recorder.Services;

public class GeminiTools : IGeminiTools
{
    private readonly string _projectDir;
    private readonly string _processName;
    private readonly string _windowTitle;
    private readonly InputUiaService _inputUiaService;

    public GeminiTools(string projectDir, string processName, string windowTitle, InputUiaService inputUiaService)
    {
        _projectDir = projectDir;
        _processName = processName;
        _windowTitle = windowTitle;
        _inputUiaService = inputUiaService;
    }

    public Task<string> AddFile(string path, string newContent)
    {
        var fullPath = Path.Combine(_projectDir, path);
        Directory.CreateDirectory(Path.GetDirectoryName(fullPath));
        File.WriteAllText(fullPath, newContent);
        return Task.FromResult($"File {path} added successfully.");
    }

    public async Task<string> Compile()
    {
        var result = await RunCommandAsync("dotnet", "build", _projectDir);
        return $"Exit Code: {result.returnCode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}";
    }

    public Task<string> DeleteFile(string path)
    {
        var fullPath = Path.Combine(_projectDir, path);
        if (File.Exists(fullPath))
        {
            File.Delete(fullPath);
            return Task.FromResult($"File {path} deleted successfully.");
        }
        return Task.FromResult($"File {path} not found.");
    }

    public async Task<string> DumpUi()
    {
        var dumpPath = Path.Combine(Path.GetTempPath(), "ui_dump.json");
        var result = await _inputUiaService.DumpUiTreeAsync(_processName, _windowTitle, dumpPath);
        if (result)
        {
            return await File.ReadAllTextAsync(dumpPath);
        }
        return "Failed to dump UI tree.";
    }

    public Task<string> ReadProject()
    {
        var sb = new StringBuilder();
        var files = Directory.GetFiles(_projectDir, "*.*", SearchOption.AllDirectories);

        foreach (var file in files)
        {
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

    public Task<string> ReplaceFile(string path, string newContent)
    {
        var fullPath = Path.Combine(_projectDir, path);
        if (File.Exists(fullPath))
        {
            File.WriteAllText(fullPath, newContent);
            return Task.FromResult($"File {path} replaced successfully.");
        }
        return Task.FromResult($"File {path} not found.");
    }

    public async Task<string> RunTest(bool record)
    {
        // Recording functionality not implemented yet.
        var result = await RunCommandAsync("dotnet", "test", _projectDir);
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