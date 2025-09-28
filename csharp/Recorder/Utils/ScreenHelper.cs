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
}