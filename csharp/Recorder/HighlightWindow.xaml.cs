using System;
using System.Windows;
using System.Drawing;
using System.Windows.Input;
using System.Windows.Media;

namespace Recorder
{
    public partial class HighlightWindow : Window
    {
        public event Action OnSelected;

        public HighlightWindow()
        {
            InitializeComponent();
        }

        public void Highlight(Rectangle rect)
        {
            var dpi = VisualTreeHelper.GetDpi(this);

            Left = rect.Left / dpi.DpiScaleX;
            Top = rect.Top / dpi.DpiScaleY;
            Width = rect.Width / dpi.DpiScaleX;
            Height = rect.Height / dpi.DpiScaleY;
            Visibility = Visibility.Visible;
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