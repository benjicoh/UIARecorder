using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;

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
        }

        private void RecordToggleButton_Checked(object sender, RoutedEventArgs e)
        {
            // TODO: Start recording logic here
        }

        private void RecordToggleButton_Unchecked(object sender, RoutedEventArgs e)
        {
            // TODO: Stop recording logic here
        }
    }
}