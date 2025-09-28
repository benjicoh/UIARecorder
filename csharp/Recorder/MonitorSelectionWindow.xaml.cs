using System.Drawing;
using System.Windows;
using System.Windows.Forms;
using System.Windows.Input;

namespace Recorder
{
    public partial class MonitorSelectionWindow : Window
    {
        public Screen SelectedMonitor { get; private set; }

        public MonitorSelectionWindow(Screen screen)
        {
            _screen = Screen.AllScreens.ElementAtOrDefault(monitorIndex) ?? Screen.PrimaryScreen;
            InitializeComponent();
            SelectedMonitor = screen;
            Left = screen.Bounds.Left;
            Top = screen.Bounds.Top;
            Width = screen.Bounds.Width;
            Height = screen.Bounds.Height;
        }

        private void OnMouseEnter(object sender, MouseEventArgs e)
        {
            HighlightBorder.Visibility = Visibility.Visible;
        }

        private void OnMouseLeave(object sender, MouseEventArgs e)
        {
            HighlightBorder.Visibility = Visibility.Collapsed;
        }

        protected override void OnMouseDown(System.Windows.Input.MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                DialogResult = true;
                Close();
            }
        }
    }
}