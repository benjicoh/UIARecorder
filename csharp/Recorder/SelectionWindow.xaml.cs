using System.Windows;
using System.Windows.Input;
using System.Drawing;
using Point = System.Windows.Point;
using Screen = System.Windows.Forms.Screen;

namespace Recorder
{
    public partial class SelectionWindow : Window
    {
        private Point _startPoint;
        public Rectangle SelectedArea { get; private set; }
        public event EventHandler<Rectangle> RegionSelected;

        public SelectionWindow(Screen screen)
        {
            InitializeComponent();
            Left = screen.Bounds.Left;
            Top = screen.Bounds.Top;
            Width = screen.Bounds.Width;
            Height = screen.Bounds.Height;
        }

        protected override void OnMouseDown(MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                _startPoint = e.GetPosition(this);
                SelectionRectangle.Visibility = Visibility.Visible;
                System.Windows.Controls.Canvas.SetLeft(SelectionRectangle, _startPoint.X);
                System.Windows.Controls.Canvas.SetTop(SelectionRectangle, _startPoint.Y);
            }
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                Point currentPoint = e.GetPosition(this);
                var rect = new Rect(_startPoint, currentPoint);
                SelectionRectangle.Width = rect.Width;
                SelectionRectangle.Height = rect.Height;
                System.Windows.Controls.Canvas.SetLeft(SelectionRectangle, rect.Left);
                System.Windows.Controls.Canvas.SetTop(SelectionRectangle, rect.Top);
            }
        }

        protected override void OnMouseUp(MouseButtonEventArgs e)
        {
            base.OnMouseUp(e);
            if (e.LeftButton == MouseButtonState.Released)
            {
                Point endPoint = e.GetPosition(this);
                var rect = new Rect(_startPoint, endPoint);

                var dpiScale = PresentationSource.FromVisual(this).CompositionTarget.TransformToDevice;
                var screenLeft = (int)(Left * dpiScale.M11);
                var screenTop = (int)(Top * dpiScale.M22);

                SelectedArea = new Rectangle(
                    screenLeft + (int)(rect.X * dpiScale.M11),
                    screenTop + (int)(rect.Y * dpiScale.M22),
                    (int)(rect.Width * dpiScale.M11),
                    (int)(rect.Height * dpiScale.M22)
                );
                RegionSelected?.Invoke(this, SelectedArea);
                Close();
            }
        }
    }
}