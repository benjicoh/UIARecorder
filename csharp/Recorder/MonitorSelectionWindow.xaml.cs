using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Forms;
using System.Drawing;
using System.Linq;
using Point = System.Windows.Point;

namespace Recorder
{
    public partial class MonitorSelectionWindow : Window
    {
        public Rectangle SelectedMonitor { get; private set; }
        private Border _highlightRectangle;

        public MonitorSelectionWindow()
        {
            InitializeComponent();
            Loaded += OnLoaded;
        }

        private void OnLoaded(object sender, RoutedEventArgs e)
        {
            var virtualScreen = SystemInformation.VirtualScreen;
            this.Left = virtualScreen.Left;
            this.Top = virtualScreen.Top;
            this.Width = virtualScreen.Width;
            this.Height = virtualScreen.Height;

            var allScreens = Screen.AllScreens;

            // Create a canvas that spans the entire virtual screen
            MonitorCanvas.Width = virtualScreen.Width;
            MonitorCanvas.Height = virtualScreen.Height;

            foreach (var screen in allScreens)
            {
                var screenBounds = screen.Bounds;

                var border = new Border
                {
                    BorderBrush = System.Windows.Media.Brushes.Transparent,
                    BorderThickness = new Thickness(2),
                    Width = screenBounds.Width,
                    Height = screenBounds.Height
                };

                Canvas.SetLeft(border, screenBounds.Left - virtualScreen.Left);
                Canvas.SetTop(border, screenBounds.Top - virtualScreen.Top);
                MonitorCanvas.Children.Add(border);
            }

            _highlightRectangle = new Border
            {
                BorderBrush = System.Windows.Media.Brushes.Red,
                BorderThickness = new Thickness(3),
                Visibility = Visibility.Collapsed
            };
            MonitorCanvas.Children.Add(_highlightRectangle);
        }

        protected override void OnMouseMove(System.Windows.Input.MouseEventArgs e)
        {
            base.OnMouseMove(e);
            var mousePosition = PointToScreen(e.GetPosition(this));
            var activeScreen = Screen.AllScreens.FirstOrDefault(s => s.Bounds.Contains(PointToDrawingPoint(mousePosition)));

            if (activeScreen != null)
            {
                var screenBounds = activeScreen.Bounds;
                var virtualScreen = SystemInformation.VirtualScreen;

                _highlightRectangle.Width = screenBounds.Width;
                _highlightRectangle.Height = screenBounds.Height;
                Canvas.SetLeft(_highlightRectangle, screenBounds.Left - virtualScreen.Left);
                Canvas.SetTop(_highlightRectangle, screenBounds.Top - virtualScreen.Top);
                _highlightRectangle.Visibility = Visibility.Visible;
            }
            else
            {
                _highlightRectangle.Visibility = Visibility.Collapsed;
            }
        }

        protected override void OnMouseDown(MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                var mousePosition = PointToScreen(e.GetPosition(this));
                var selectedScreen = Screen.AllScreens.FirstOrDefault(s => s.Bounds.Contains(PointToDrawingPoint(mousePosition)));

                if (selectedScreen != null)
                {
                    SelectedMonitor = selectedScreen.Bounds;
                    DialogResult = true;
                    Close();
                }
            }
        }

        private System.Drawing.Point PointToDrawingPoint(Point point)
        {
            return new System.Drawing.Point((int)point.X, (int)point.Y);
        }
    }
}