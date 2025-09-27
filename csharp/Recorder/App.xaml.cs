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
            services.AddSingleton<MainViewModel>();
            services.AddTransient<RecordingService>();

            services.AddLogging(builder =>
            {
                builder.AddProvider(new ObservableLoggerProvider(message =>
                {
                    var mainViewModel = ServiceProvider.GetService<MainViewModel>();
                    App.Current.Dispatcher.BeginInvoke(System.Windows.Threading.DispatcherPriority.Background, new Action(() =>
                    {
                        mainViewModel?.LogMessages.Add(message);
                    }));
                }));
            });
            
            services.AddSingleton<MainWindow>();
        }

        public IServiceProvider ServiceProvider { get; }

        //protected override void OnStartup(StartupEventArgs e)
        //{
        //    base.OnStartup(e);

        //    var mainWindow = _serviceProvider.GetService<MainWindow>();
        //    mainWindow.DataContext = _serviceProvider.GetService<MainViewModel>();
        //    mainWindow.Show();
        //}
    }
}