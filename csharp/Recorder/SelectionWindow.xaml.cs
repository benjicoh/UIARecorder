using System.Windows;
using System.Windows.Input;
using System.Drawing;
using Point = System.Windows.Point;
using Recorder.ViewModels;

namespace Recorder
{
    public partial class SelectionWindow : Window
    {
        private Point _startPoint;
        private readonly SelectionViewModel _viewModel;

        public SelectionWindow(SelectionViewModel viewModel)
        {
            InitializeComponent();
            _viewModel = viewModel;
            DataContext = _viewModel;
        }

        public Rectangle SelectedArea => _viewModel.SelectedArea;

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
                _viewModel.SelectedArea = new Rectangle(
                    (int)(rect.X * dpiScale.M11),
                    (int)(rect.Y * dpiScale.M22),
                    (int)(rect.Width * dpiScale.M11),
                    (int)(rect.Height * dpiScale.M22)
                );
                DialogResult = true;
                Close();
            }
        }
    }
}