using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;

namespace Recorder.Utils
{
    public static class ScreenHelper
    {
        public static IEnumerable<Screen> GetAllScreens()
        {
            return Screen.AllScreens.ToList();
        }

        public static Rectangle GetVirtualScreenBounds()
        {
            return SystemInformation.VirtualScreen;
        }
    }

    public class SelectionResult
    {
        public int SelectedMonitor { get; set; } = 0;
        public Rectangle SelectedArea { get; set; } = Rectangle.Empty;
        public IntPtr SelectedWindowHandle { get; set; } = IntPtr.Zero;
        public string WindowTitle { get; set; }

        public string ProcessName { get; set; } = string.Empty;

        public void MakeDivisableBy2()
        {
            if (SelectedArea.Width % 2 != 0)
            {
                SelectedArea = new Rectangle(SelectedArea.X, SelectedArea.Y, SelectedArea.Width - 1, SelectedArea.Height);
            }
            if (SelectedArea.Height % 2 != 0)
            {
                SelectedArea = new Rectangle(SelectedArea.X, SelectedArea.Y, SelectedArea.Width, SelectedArea.Height - 1);
            }
        }
    }
}