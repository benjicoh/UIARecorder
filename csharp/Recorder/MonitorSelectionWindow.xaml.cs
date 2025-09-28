using System.Drawing;
using System.Windows;
using System.Windows.Forms;
using System.Windows.Input;

namespace Recorder
{
    public partial class MonitorSelectionWindow : Window
    {
        public Rectangle SelectedArea { get; private set; }

        public int MonitorID
        {
            get; set;
        }

        public MonitorSelectionWindow(Screen screen, int monitorID)
        {
            InitializeComponent();
            SelectedArea = screen.Bounds;
            Left = screen.Bounds.Left;
            Top = screen.Bounds.Top;
            Width = screen.Bounds.Width;
            Height = screen.Bounds.Height;
            MonitorID = monitorID;
        }

        private void OnMouseEnter(object sender, System.Windows.Input.MouseEventArgs e)
        {
            HighlightBorder.Visibility = Visibility.Visible;
        }

        private void OnMouseLeave(object sender, System.Windows.Input.MouseEventArgs e)
        {
            HighlightBorder.Visibility = Visibility.Collapsed;
        }

    }
}