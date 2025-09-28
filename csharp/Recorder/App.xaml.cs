using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Recorder.Logging;
using Recorder.Services;
using Recorder.ViewModels;
using System;
using System.Windows;

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
                provider.GetRequiredService<ILogger<MainViewModel>>()
            ));
            services.AddTransient<RecordingService>();
            services.AddSingleton<ThreadManager>();
            services.AddSingleton<InputUiaService>();
            services.AddSingleton<OverlayService>();
            services.AddSingleton<AnnotationService>();

            services.AddLogging(builder =>
            {
                builder.AddProvider(new ObservableLoggerProvider(message =>
                {
                    if (ServiceProvider?.GetService<MainViewModel>() is MainViewModel mainViewModel)
                    {
                        Current.Dispatcher.BeginInvoke(() =>
                        {
                            mainViewModel.LogMessages.Add(message);
                        });
                    }
                }));
            });
            
            services.AddSingleton<MainWindow>();
        }

        public IServiceProvider ServiceProvider { get; }

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            var mainViewModel = ServiceProvider.GetService<MainViewModel>();

            if (e.Args.Length > 0)
            {
                mainViewModel.OutputPath = e.Args[0];
            }

            var mainWindow = ServiceProvider.GetService<MainWindow>();
            mainWindow.Show();
        }
    }
}