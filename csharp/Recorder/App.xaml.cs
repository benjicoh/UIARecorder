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
            services.AddSingleton(provider => new MainViewModel(
                provider.GetRequiredService<RecordingService>(),
                provider.GetRequiredService<InputUiaService>(),
                provider.GetRequiredService<AnnotationService>(),
                provider.GetRequiredService<ThreadManager>(),
                provider.GetRequiredService<ILogger<MainViewModel>>(),
                provider.GetRequiredService<GeminiTestGenerator>(),
                provider.GetRequiredService<ConfigurationService>(),
                provider.GetRequiredService<WindowSelector>(),
                provider.GetRequiredService<ConsoleWindow>(),
                provider.GetRequiredService<IAlertService>()
            ));

            services.AddSingleton(provider => new GeminiTestGenerator(
                provider.GetRequiredService<ILogger<GeminiTestGenerator>>(),
                provider.GetRequiredService<InputUiaService>(),
                provider.GetRequiredService<IAskHumanService>()
            ));
            services.AddSingleton<IAlertService, AlertService>();
            services.AddSingleton<IAskHumanService, AskHumanService>();
            services.AddSingleton<ConfigurationService>();
            services.AddSingleton<RecordingService>();
            services.AddSingleton<ThreadManager>();
            services.AddSingleton<InputUiaService>();
            services.AddSingleton<OverlayService>();
            services.AddSingleton<AnnotationService>();
            services.AddSingleton<WindowSelector>();
            services.AddSingleton<MainWindow>();
            services.AddSingleton<ConsoleWindow>();

            services.AddLogging(builder =>
            {
                builder.AddProvider(new ObservableLoggerProvider(logEntry =>
                {
                    var mainViewModel = ServiceProvider.GetService<MainViewModel>();
                    if (mainViewModel != null)
                    {
                        App.Current.Dispatcher.BeginInvoke(System.Windows.Threading.DispatcherPriority.Background, new Action(() =>
                        {
                            mainViewModel.LogMessages.Add(logEntry);
                        }));
                    }
                }));
            });

            //set log level to debug
            services.Configure<LoggerFilterOptions>(options => options.MinLevel = LogLevel.Debug);

        }

        public IServiceProvider ServiceProvider { get; }

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            Win32Utils.SetProcessDpiAwarenessContext(Win32Utils.DPI_AWARENESS_CONTEXT.DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2);

            var mainViewModel = ServiceProvider.GetService<MainViewModel>();

            var mainWindow = new MainWindow(ServiceProvider.GetRequiredService<IAlertService>());
            var consoleWindow = ServiceProvider.GetService<ConsoleWindow>();

            consoleWindow.DataContext = mainViewModel;
            mainWindow.Show();
            consoleWindow.Show();
        }
    }
}