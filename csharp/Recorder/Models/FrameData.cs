using OpenCvSharp;
using System;
using System.Collections.Generic;

namespace Recorder.Models
{
    public class FrameData
    {
        public Mat Frame { get; }
        public DateTime Timestamp { get; }

        public FrameData(Mat frame, DateTime timestamp)
        {
            Frame = frame;
            Timestamp = timestamp;
        }
    }
}