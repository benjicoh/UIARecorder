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
        private IServiceProvider _serviceProvider;

        public App()
        {
            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            _serviceProvider = serviceCollection.BuildServiceProvider();
        }

        private void ConfigureServices(IServiceCollection services)
        {
            services.AddSingleton<MainViewModel>();
            services.AddTransient<RecordingService>();

            services.AddLogging(builder =>
            {
                builder.AddProvider(new ObservableLoggerProvider(message =>
                {
                    var mainViewModel = _serviceProvider.GetService<MainViewModel>();
                    mainViewModel?.LogMessages.Add(message);
                }));
            });

            services.AddSingleton<MainWindow>();
        }

        protected override void OnStartup(StartupEventArgs e)
        {
            base.OnStartup(e);

            var mainWindow = _serviceProvider.GetService<MainWindow>();
            mainWindow.DataContext = _serviceProvider.GetService<MainViewModel>();
            mainWindow.Show();
        }
    }
}