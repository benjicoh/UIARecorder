using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Recorder.Logging;
using Recorder.Services;
using Recorder.Utils;
using Recorder.ViewModels;
using System;
using System.Windows;
using System.Threading.Tasks;
using System.Threading;

namespace Recorder
{
    public partial class App : Application
    {
        public App()
        {
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            ServiceProvider = serviceCollection.BuildServiceProvider();
        }

        private void ConfigureServices(IServiceCollection services)
        {
            //services
            services.AddSingleton<IAlertService, AlertService>();
            services.AddSingleton<IAskHumanService, AskHumanService>();
            services.AddSingleton<GeminiTestGenerator>();
            services.AddSingleton<ConfigurationService>();
            services.AddSingleton<RecordingService>();
            services.AddSingleton<InputUiaService>();
            services.AddSingleton<OverlayService>();
            services.AddSingleton<AnnotationService>();
            //utils
            services.AddSingleton<GeminiTools>();
            services.AddSingleton<ThreadManager>();
            services.AddSingleton<WindowSelector>();
            //vms
            services.AddSingleton<MainViewModel>();
            //views
            services.AddSingleton<MainWindow>();
            //logging
            services.AddLogging(builder =>
            {
                builder.AddProvider(new ObservableLoggerProvider(logEntry =>
                {
                    //log to file
                    System.IO.File.AppendAllText("app.log", $"{logEntry.Timestamp:yyyy-MM-dd HH:mm:ss.fff} [{logEntry.CallerFilePath}:{logEntry.CallerLineNumber}] [{logEntry.Level}] {logEntry.Message}{Environment.NewLine}");
                    if (logEntry.Exception != null)
                    {
                        System.IO.File.AppendAllText("app.log", $"Exception : {logEntry.Exception}{Environment.NewLine}");
                    }

                    //log to console
                    var consoleColor = Console.ForegroundColor;
                    switch (logEntry.Level)
                    {
                        case LogLevel.Trace:
                        case LogLevel.Debug:
                            Console.ForegroundColor = ConsoleColor.DarkGray;
                            break;
                        case LogLevel.Information:
                            Console.ForegroundColor = ConsoleColor.White;
                            break;
                        case LogLevel.Warning:
                            Console.ForegroundColor = ConsoleColor.Yellow;
                            break;
                        case LogLevel.Error:
                        case LogLevel.Critical:
                            Console.ForegroundColor = ConsoleColor.Red;
                            break;
                        default:
                            break;
                    }
                            
                    Console.WriteLine($"{logEntry.Timestamp:yyyy-MM-dd HH:mm:ss.fff} [{logEntry.CallerFilePath}:{logEntry.CallerLineNumber}] [{logEntry.Level}] {logEntry.Message}");
                    if (logEntry.Exception != null)
                    {
                        Console.WriteLine($"Exception : {logEntry.Exception}");
                    }
                    Console.ForegroundColor = consoleColor;
                    
                }));
            });

            //set log level to debug
            services.Configure<LoggerFilterOptions>(options => options.MinLevel = LogLevel.Debug);

            

        }

        public IServiceProvider ServiceProvider { get; }

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);
            //delete log file if exists
            if (System.IO.File.Exists("app.log"))
            {
                System.IO.File.Delete("app.log");
            }
            //show console window
            Win32Utils.AllocConsole();
            
            var mainWindow = ServiceProvider.GetService<MainWindow>();
            mainWindow.Show();
        }
    }
}