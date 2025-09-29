using System;
using System.IO;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Recorder.Models;

namespace Recorder.Services
{
    public class ConfigurationService
    {
        private readonly string _configFilePath;
        private readonly ILogger<ConfigurationService> _logger;
        public Configuration Config { get; private set; }

        public ConfigurationService(ILogger<ConfigurationService> logger)
        {
            _logger = logger;
            _configFilePath = Path.Combine(AppContext.BaseDirectory, "config.json");
            LoadConfig();
        }

        private void LoadConfig()
        {
            try
            {
                if (File.Exists(_configFilePath))
                {
                    var json = File.ReadAllText(_configFilePath);
                    Config = JsonSerializer.Deserialize<Configuration>(json);
                    _logger.LogInformation("Configuration loaded from {path}", _configFilePath);
                }
                else
                {
                    _logger.LogInformation("Configuration file not found. Creating a new one with default settings.");
                    Config = new Configuration();
                    SaveConfig();
                }
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error loading configuration. Using default settings.");
                Config = new Configuration();
            }
        }

        public void SaveConfig()
        {
            try
            {
                var options = new JsonSerializerOptions { WriteIndented = true };
                var json = JsonSerializer.Serialize(Config, options);
                File.WriteAllText(_configFilePath, json);
                _logger.LogInformation("Configuration saved to {path}", _configFilePath);
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error saving configuration.");
            }
        }
    }
}