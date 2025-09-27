using System.Drawing;
using System.IO;
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
using Sdcb;

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
        private CancellationTokenSource? cts;

        private void RecordToggleButton_Checked(object sender, RoutedEventArgs e)
        {
            cts = new CancellationTokenSource();
            // TODO: Start recording logic here
            foreach (var frame in ScreenCapture.CaptureScreenFrames(0, 20.0, 0, cts.Token))
            {
                //Convert frame pointer to bitmap
                nint ptr = frame.DataPointer;
                int w = frame.Width;
                int h = frame.Height;
                using Bitmap bitmap = new(w, h, frame.RowPitch, System.Drawing.Imaging.PixelFormat.Format32bppArgb, ptr);
                //Save bitmap to file
                string fileName = System.IO.Path.Combine("captures", $"capture_{DateTime.Now:yyyyMMdd_HHmmss_fff}.png");
                Directory.CreateDirectory("captures");
                bitmap.Save(fileName, System.Drawing.Imaging.ImageFormat.Png);
            }

        }   

        private void RecordToggleButton_Unchecked(object sender, RoutedEventArgs e)
        {
            cts?.Cancel();
        }
    }
}