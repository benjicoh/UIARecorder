using System;
using System.Windows;
using System.Drawing;
using System.Windows.Input;

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
            Left = rect.Left;
            Top = rect.Top;
            Width = rect.Width;
            Height = rect.Height;
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