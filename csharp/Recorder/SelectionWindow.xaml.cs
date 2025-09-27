using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using FlaUI.Core.AutomationElements;
using FlaUI.UIA3;
using System.Drawing;
using Window = System.Windows.Window;
using Point = System.Windows.Point;

namespace Recorder
{
    public partial class SelectionWindow : Window
    {
        public enum SelectionMode
        {
            Region,
            Window
        }

        public System.Drawing.Rectangle SelectedArea { get; private set; }
        private Point _startPoint;
        private readonly SelectionMode _mode;
        private readonly UIA3Automation _automation;
        private AutomationElement _hoveredWindow;

        public SelectionWindow(SelectionMode mode)
        {
            InitializeComponent();
            _mode = mode;
            if (_mode == SelectionMode.Window)
            {
                _automation = new UIA3Automation();
            }
        }

        protected override void OnMouseDown(MouseButtonEventArgs e)
        {
            base.OnMouseDown(e);
            if (e.LeftButton == MouseButtonState.Pressed)
            {
                if (_mode == SelectionMode.Region)
                {
                    _startPoint = e.GetPosition(this);
                    SelectionRectangle.Visibility = Visibility.Visible;
                    Canvas.SetLeft(SelectionRectangle, _startPoint.X);
                    Canvas.SetTop(SelectionRectangle, _startPoint.Y);
                }
                else // Window mode
                {
                    if (_hoveredWindow != null)
                    {
                        SelectedArea = _hoveredWindow.Properties.BoundingRectangle.Value;
                        DialogResult = true;
                        Close();
                    }
                }
            }
        }

        protected override void OnMouseMove(MouseEventArgs e)
        {
            base.OnMouseMove(e);
            if (_mode == SelectionMode.Region)
            {
                if (e.LeftButton == MouseButtonState.Pressed)
                {
                    Point currentPoint = e.GetPosition(this);
                    var rect = new Rect(_startPoint, currentPoint);
                    SelectionRectangle.Width = rect.Width;
                    SelectionRectangle.Height = rect.Height;
                    Canvas.SetLeft(SelectionRectangle, rect.Left);
                    Canvas.SetTop(SelectionRectangle, rect.Top);
                }
            }
            else // Window mode
            {
                Point currentPoint = e.GetPosition(this);
                _hoveredWindow = _automation.FromPoint(new System.Drawing.Point((int)currentPoint.X, (int)currentPoint.Y))?.AsWindow();
                if (_hoveredWindow != null)
                {
                    var rect = _hoveredWindow.Properties.BoundingRectangle.Value;
                    SelectionRectangle.Width = rect.Width;
                    SelectionRectangle.Height = rect.Height;
                    Canvas.SetLeft(SelectionRectangle, rect.Left);
                    Canvas.SetTop(SelectionRectangle, rect.Top);
                    SelectionRectangle.Visibility = Visibility.Visible;
                }
                else
                {
                    SelectionRectangle.Visibility = Visibility.Collapsed;
                }
            }
        }

        protected override void OnMouseUp(MouseButtonEventArgs e)
        {
            base.OnMouseUp(e);
            if (e.LeftButton == MouseButtonState.Released && _mode == SelectionMode.Region)
            {
                Point endPoint = e.GetPosition(this);
                var rect = new Rect(_startPoint, endPoint);
                var dpiScale = PresentationSource.FromVisual(this).CompositionTarget.TransformToDevice;
                SelectedArea = new System.Drawing.Rectangle(
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