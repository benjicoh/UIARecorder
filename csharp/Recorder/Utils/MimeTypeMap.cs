using System.Collections.Generic;

namespace Recorder.Utils
{
    public static class MimeTypeMap
    {
        private static readonly Dictionary<string, string> _mappings = new Dictionary<string, string>(System.StringComparer.InvariantCultureIgnoreCase)
        {
            {".mp4", "video/mp4"},
            {".json", "application/json"},
            {".txt", "text/plain"},
            {".cs", "text/plain"},
            {".csproj", "text/plain"},
            {".png", "image/png"},
            // Add more mappings as needed
        };

        public static string GetMimeType(string extension)
        {
            if (extension == null)
            {
                throw new System.ArgumentNullException(nameof(extension));
            }

            if (!extension.StartsWith("."))
            {
                extension = "." + extension;
            }

            return _mappings.TryGetValue(extension, out string mime) ? mime : "application/octet-stream";
        }
    }
}