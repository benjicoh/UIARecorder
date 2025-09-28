using System;
using System.Windows;
using System.Drawing;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Forms;

namespace Recorder
{
    public partial class HighlightWindow : Window
    {
        public event Action OnSelected;
        public Screen Screen { get; }

        public HighlightWindow(Screen screen)
        {
            InitializeComponent();
            Screen = screen;
            Left = screen.Bounds.Left;
            Top = screen.Bounds.Top;
            Width = screen.Bounds.Width;
            Height = screen.Bounds.Height;
            Title = $"HighlightWindow_{screen.DeviceName}";
        }

        public void Highlight(Rectangle rect)
        {
            var dpi = VisualTreeHelper.GetDpi(this);
            var dpiScaleX = dpi.DpiScaleX;
            var dpiScaleY = dpi.DpiScaleY;

            var highlightRect = new Rectangle(
                (int)(rect.X / dpiScaleX),
                (int)(rect.Y / dpiScaleY),
                (int)(rect.Width / dpiScaleX),
                (int)(rect.Height / dpiScaleY)
            );

            border.Margin = new Thickness(
                highlightRect.Left - (int)(Screen.Bounds.Left / dpiScaleX),
                highlightRect.Top - (int)(Screen.Bounds.Top / dpiScaleY),
                0,
                0
            );

            border.Width = highlightRect.Width;
            border.Height = highlightRect.Height;
            border.Visibility = Visibility.Visible;
        }

        public void Hide()
        {
            if (border.Visibility == Visibility.Visible)
            {
                border.Visibility = Visibility.Collapsed;
            }
        }

        protected override void OnMouseDown(MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                OnSelected?.Invoke();
                Close();
            }
        }

        protected override void OnKeyDown(KeyEventArgs e)
        {
            base.OnKeyDown(e);
            if (e.Key == Key.Escape)
            {
                DialogResult = false;
                Close();
            }
        }
    }
}