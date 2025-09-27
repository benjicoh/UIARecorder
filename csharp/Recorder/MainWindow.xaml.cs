using System.Windows;

namespace Recorder
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
            //get the singleton from the app.xaml.cs
            
            DataContext = (App.Current as App).ServiceProvider.GetService(typeof(ViewModels.MainViewModel));
        }
    }
}