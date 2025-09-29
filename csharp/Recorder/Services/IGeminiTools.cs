using GenerativeAI.Tools;
using System.ComponentModel;
using System.Threading.Tasks;

namespace Recorder.Services;

[GenerateJsonSchema(GoogleFunctionTool = true)]
public interface IGeminiTools
{
    [Description("read project - returns a markdown of all cs, csproj files under the project directory")]
    Task<string> ReadProject();

    [Description("replace file (path, new content)")]
    Task<string> ReplaceFile(
        [Description("path of the file to be replaced")]
        string path,
        [Description("new content of the file")]
        string newContent);

    [Description("add file (path, new content)")]
    Task<string> AddFile(
        [Description("path of the file to be added")]
        string path,
        [Description("content of the file to be added")]
        string newContent);

    [Description("delete file (path)")]
    Task<string> DeleteFile(
        [Description("path of the file to be deleted")]
        string path);

    [Description("compile (returns compilation result)")]
    Task<string> Compile();

    [Description("run test(bool record) (returns test result, if record true - captures and returns videos)")]
    Task<string> RunTest(
        [Description("if true, captures and returns videos")]
        bool record);

    [Description("dump ui (returns json dump)")]
    Task<string> DumpUi();
}