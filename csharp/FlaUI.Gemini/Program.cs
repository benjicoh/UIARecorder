using FlaUI.Gemini.Models;
using Google.GenerativeAI.Core;
using Google.GenerativeAI.GenerativeAI;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading.Tasks;

namespace FlaUI.Gemini
{
    class Program
    {
        static async Task Main(string[] args)
        {
            if (args.Length == 0)
            {
                Console.WriteLine("Please provide the path to the recording folder.");
                return;
            }

            var recordingPath = args[0];
            var annotationsPath = Path.Combine(recordingPath, "annotations.json");

            if (!File.Exists(annotationsPath))
            {
                Console.WriteLine($"Annotations file not found at: {annotationsPath}");
                return;
            }

            var json = await File.ReadAllTextAsync(annotationsPath);
            var annotations = JsonConvert.DeserializeObject<List<ElementInfo>>(json);

            Console.WriteLine($"Loaded {annotations.Count} root elements from the recording.");

            try
            {
                await ProcessWithGemini(annotations);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"An error occurred while processing with Gemini: {ex.Message}");
            }
        }

        static async Task ProcessWithGemini(List<ElementInfo> elements)
        {
            var apiKey = Environment.GetEnvironmentVariable("GEMINI_API_KEY");
            if (string.IsNullOrEmpty(apiKey))
            {
                Console.WriteLine("Error: The GEMINI_API_KEY environment variable is not set.");
                return;
            }

            var model = new GenerativeModel(apiKey: apiKey, model: "gemini-1.5-flash");

            var prompt = BuildPrompt(elements);

            Console.WriteLine("\nSending prompt to Gemini...");
            var response = await model.GenerateContentAsync(prompt);

            Console.WriteLine("\nGemini Response:");
            Console.WriteLine(response.Text);
        }

        static string BuildPrompt(List<ElementInfo> elements)
        {
            var sb = new StringBuilder();
            sb.AppendLine("You are an expert at analyzing UI automation data. Based on the following JSON data, describe the sequence of actions the user took. Focus on the events and the elements they were performed on.");
            sb.AppendLine("Provide a clear, step-by-step summary of the user's journey.");
            sb.AppendLine("\n```json");
            sb.AppendLine(JsonConvert.SerializeObject(elements, Formatting.Indented));
            sb.AppendLine("```");
            return sb.ToString();
        }
    }
}