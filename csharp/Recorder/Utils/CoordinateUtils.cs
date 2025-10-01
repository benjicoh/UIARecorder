using FlaUI.Core.AutomationElements;
using System.Drawing;

namespace Recorder.Utils
{
    public static class CoordinateUtils
    {
        /// <summary>
        /// Transforms a point from absolute screen coordinates to be relative to a given capture area.
        /// </summary>
        /// <param name="screenPoint">The point in screen coordinates.</param>
        /// <param name="captureArea">The capture area rectangle.</param>
        /// <returns>A new point relative to the top-left of the capture area.</returns>
        public static Point TransformFromScreen(Point screenPoint, Rectangle captureArea)
        {
            return new Point(screenPoint.X - captureArea.X, screenPoint.Y - captureArea.Y);
        }

        public static Rectangle TransformFromScreen(Rectangle screenRect, Rectangle captureArea)
        {
            return new Rectangle(
                screenRect.X - captureArea.X,
                screenRect.Y - captureArea.Y,
                screenRect.Width,
                screenRect.Height);
        }


        public static Point TransformToElement(Point screenPoint, AutomationElement element)
        {
            var elementRec = element.GetSafeBoundingRectangle();
            return new Point(screenPoint.X - elementRec.X, screenPoint.Y - elementRec.Y);
        }

        
        /// <summary>
        /// Transforms a point from relative capture area coordinates to absolute screen coordinates.
        /// </summary>
        /// <param name="relativePoint">The point relative to the capture area.</param>
        /// <param name="captureArea">The capture area rectangle.</param>
        /// <returns>A new point in absolute screen coordinates.</returns>
        public static Point TransformToScreen(Point relativePoint, Rectangle captureArea)
        {
            return new Point(relativePoint.X + captureArea.X, relativePoint.Y + captureArea.Y);
        }
    }
}