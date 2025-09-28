using System.Windows;
using System.Windows.Input;
using System.Drawing;
using Point = System.Windows.Point;
using Recorder.ViewModels;
using System.Windows.Forms;

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
            this.Loaded += OnLoaded;
        }

        private void OnLoaded(object sender, RoutedEventArgs e)
        {
            var virtualScreen = SystemInformation.VirtualScreen;
            var source = PresentationSource.FromVisual(this);
            if (source?.CompositionTarget == null) return;
            var dpiX = source.CompositionTarget.TransformToDevice.M11;
            var dpiY = source.CompositionTarget.TransformToDevice.M22;

            this.Left = virtualScreen.Left / dpiX;
            this.Top = virtualScreen.Top / dpiY;
            this.Width = virtualScreen.Width / dpiX;
            this.Height = virtualScreen.Height / dpiY;
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
                SelectionRectangle.Width = 0;
                SelectionRectangle.Height = 0;
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

                var source = PresentationSource.FromVisual(this);
                if (source?.CompositionTarget == null)
                {
                    DialogResult = false;
                    Close();
                    return;
                }

                var topLeftOnScreen = PointToScreen(rect.TopLeft);
                var dpiScale = source.CompositionTarget.TransformToDevice;

                var pixelX = topLeftOnScreen.X * dpiScale.M11;
                var pixelY = topLeftOnScreen.Y * dpiScale.M22;
                var pixelWidth = rect.Width * dpiScale.M11;
                var pixelHeight = rect.Height * dpiScale.M22;

                _viewModel.SelectedArea = new Rectangle(
                    (int)pixelX,
                    (int)pixelY,
                    (int)pixelWidth,
                    (int)pixelHeight
                );

                DialogResult = true;
                Close();
            }
        }
    }
}