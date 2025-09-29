using CSharpToJsonSchema;
using GenerativeAI.Tools;
using System.ComponentModel;
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
    Task<string> RunTest(
        [Description("if true, captures and returns videos")]
        bool record,
        CancellationToken cancellationToken = default);

    [Description("Dumps the UI, returns JSON dump")]
    Task<string> DumpUi(CancellationToken cancellationToken = default);
}