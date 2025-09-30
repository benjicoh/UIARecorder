using CSharpToJsonSchema;
using GenerativeAI.Tools;
using System.ComponentModel;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace Recorder.Services;

[GenerateJsonSchema(GoogleFunctionTool = true)]
public interface IGeminiTools
{
    [Description("Reads entire project - returns a markdown of all cs, csproj files under the project directory")]
    Task<string> ReadProject(CancellationToken cancellationToken = default);

    [Description("Replaces a file in the project")]
    Task<string> ReplaceFile(
        [Description("Path of the file to be replaced - relative to the project root")]
        string path,
        [Description("New content of the file")]
        string newContent,
        CancellationToken cancellationToken = default);

    [Description("Adds a file to the project")]
    Task<string> AddFile(
        [Description("Path of the file to be added - relative to the project root")]
        string path,
        [Description("Content of the file to be added")]
        string newContent,
        CancellationToken cancellationToken = default);

    [Description("Deletes a file from the project")]
    Task<string> DeleteFile(
        [Description("Path of the file to be deleted - relative to the project root")]
        string path,
        CancellationToken cancellationToken = default);

    [Description("Compiles the project, returns the compilation result")]
    Task<string> Compile(CancellationToken cancellationToken = default);

    [Description("Runs a test, returns the test output")]
    Task<string> RunTest(CancellationToken cancellationToken = default);

    [Description("Runs a command line with arguments, returns exit code, the stdout and stderr output. Current working directory is the project root")]
    Task<string> RunCommandLine(
        [Description("Command to run, e.g. dotnet, git, etc.")]
        string cmd, 
        [Description("Arguments to pass to the command")]
        string args, 
        CancellationToken cancellationToken = default);

    [Description("Generates a json of current UI automation structure, helpful when the test fails")]
    Task<string> DumpUiAutomationTree(CancellationToken cancellationToken = default);

    [Description("Take screenshot of the current desktop")]
    Task<string> TakeScreenshot(CancellationToken cancellationToken = default);

    [Description("Logs a thought that the user needs to know about")]
    Task<string> LogThought(string thought, CancellationToken cancellationToken = default);

    [Description("Asks human for help")]
    Task<string> AskHuman(
        [Description("Question to ask human")]
        string question,
        CancellationToken cancellationToken = default);
}