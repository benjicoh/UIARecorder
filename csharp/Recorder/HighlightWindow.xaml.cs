using System;
using System.Windows;
using System.Drawing;
using System.Windows.Input;
using System.Windows.Forms;
using System.Windows.Controls;

namespace Recorder
{
    public partial class HighlightWindow : Window
    {
        public event Action OnSelected;

        public HighlightWindow()
        {
            InitializeComponent();
            this.Loaded += OnLoaded;
        }

        private void OnLoaded(object sender, RoutedEventArgs e)
        {
            var virtualScreen = SystemInformation.VirtualScreen;
            this.Left = virtualScreen.Left;
            this.Top = virtualScreen.Top;
            this.Width = virtualScreen.Width;
            this.Height = virtualScreen.Height;
        }

        public void Highlight(Rectangle rect)
        {
            if (rect.IsEmpty)
            {
                HighlightBorder.Visibility = Visibility.Collapsed;
                return;
            }

            var virtualScreen = SystemInformation.VirtualScreen;
            Canvas.SetLeft(HighlightBorder, rect.Left - virtualScreen.Left);
            Canvas.SetTop(HighlightBorder, rect.Top - virtualScreen.Top);
            HighlightBorder.Width = rect.Width;
            HighlightBorder.Height = rect.Height;
            HighlightBorder.Visibility = Visibility.Visible;
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