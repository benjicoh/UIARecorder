using System;
using System.Drawing;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Forms;
using System.Windows.Input;
using System.Windows.Media;
using Point = System.Windows.Point;

namespace Recorder
{
    public partial class MonitorSelectionWindow : Window
    {
        
        public Rectangle SelectedMonitor { get; private set; }
        private Border _highlightRectangle;
        private Screen _screen;

        public MonitorSelectionWindow(int monitorIndex)
        {
            _screen = Screen.AllScreens.ElementAtOrDefault(monitorIndex) ?? Screen.PrimaryScreen;
            InitializeComponent();
            Loaded += OnLoaded;
        }


        private void OnLoaded(object sender, RoutedEventArgs e)
        {
            this.Top = _screen.Bounds.Top;
            this.Left = _screen.Bounds.Left;
            this.Width = _screen.Bounds.Width;
            this.Height = _screen.Bounds.Height;

            // Create a canvas that spans the entire virtual screen
            MonitorCanvas.Width = _screen.Bounds.Width;
            MonitorCanvas.Height = _screen.Bounds.Height;

            _highlightRectangle = new Border
            {
                BorderBrush = System.Windows.Media.Brushes.Red,
                BorderThickness = new Thickness(3),
                Visibility = Visibility.Collapsed
            };
            MonitorCanvas.Children.Add(_highlightRectangle);
        }

        // Use MonitorFromPoint and GetMonitorInfo to get monitor under mouse

        protected override void OnMouseEnter(System.Windows.Input.MouseEventArgs e)
        {
            base.OnMouseEnter(e);
            _highlightRectangle.Visibility = Visibility.Visible;
        }

        protected override void OnMouseLeave(System.Windows.Input.MouseEventArgs e)
        {
            base.OnMouseLeave(e);
            _highlightRectangle.Visibility = Visibility.Collapsed;
        }

        protected override void OnMouseDown(System.Windows.Input.MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                SelectedMonitor = _screen.Bounds;
                DialogResult = true;
                Close();
            }
        }
    }
}