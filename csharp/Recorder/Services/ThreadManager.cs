using Recorder.Utils;
using System;
using System.Collections.Generic;

namespace Recorder.Services
{
    public class ThreadManager : IDisposable
    {
        public DedicatedThread AudioCaptureThread { get; }
        public DedicatedThread InputUiaThread { get; }
        public DedicatedThread VideoCaptureThread { get; }
        public DedicatedThread VideoProcessingThread { get; }

        private readonly List<DedicatedThread> _threads = new List<DedicatedThread>();

        public ThreadManager()
        {
            AudioCaptureThread = new DedicatedThread();
            InputUiaThread = new DedicatedThread(isSta: true);
            VideoCaptureThread = new DedicatedThread(isSta: true);
            VideoProcessingThread = new DedicatedThread();

            _threads.Add(AudioCaptureThread);
            _threads.Add(InputUiaThread);
            _threads.Add(VideoCaptureThread);
            _threads.Add(VideoProcessingThread);
        }

        public void StartAll()
        {
            foreach (var thread in _threads)
            {
                thread.Start();
            }
        }

        public void StopAll()
        {
            foreach (var thread in _threads)
            {
                thread.Stop();
            }
        }

        public void Dispose()
        {
            foreach (var thread in _threads)
            {
                thread.Dispose();
            }
        }
    }
}