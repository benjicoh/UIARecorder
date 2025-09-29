using Microsoft.Extensions.Logging;
using System;
using System.Globalization;
using System.Windows.Data;
using System.Windows.Media;

namespace Recorder.Utils
{
    public class LogLevelToBrushConverter : IValueConverter
    {
        public object Convert(object value, Type targetType, object parameter, CultureInfo culture)
        {
            if (value is LogLevel logLevel)
            {
                switch (logLevel)
                {
                    case LogLevel.Trace:
                        return Brushes.Gray;
                    case LogLevel.Debug:
                        return Brushes.Gray;
                    case LogLevel.Information:
                        return Brushes.White;
                    case LogLevel.Warning:
                        return Brushes.Yellow;
                    case LogLevel.Error:
                        return Brushes.Red;
                    case LogLevel.Critical:
                        return Brushes.Magenta;
                    default:
                        return Brushes.White;
                }
            }
            return Brushes.White;
        }

        public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        {
            throw new NotImplementedException();
        }
    }
}