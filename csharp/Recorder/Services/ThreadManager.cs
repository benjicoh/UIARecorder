using Recorder.Utils;
using System;
using System.Collections.Generic;

namespace Recorder.Services
{
    public class ThreadManager : IDisposable
    {
        public DedicatedThread AudioCaptureThread { get; private set; }
        public DedicatedThread InputUiaThread { get; private set; }
        public DedicatedThread VideoCaptureThread { get; private set; }
        public DedicatedThread VideoProcessingThread { get; private set; }

        private readonly List<DedicatedThread> _threads = new List<DedicatedThread>();

        public ThreadManager() { }

        public void StartAll()
        {
            AudioCaptureThread = new DedicatedThread();
            InputUiaThread = new DedicatedThread(isSta: true);
            VideoCaptureThread = new DedicatedThread(isSta: true);
            VideoProcessingThread = new DedicatedThread();

            _threads.Clear();
            _threads.Add(AudioCaptureThread);
            _threads.Add(InputUiaThread);
            _threads.Add(VideoCaptureThread);
            _threads.Add(VideoProcessingThread);

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
            _threads.Clear();
        }

        public void Dispose()
        {
            foreach (var thread in _threads)
            {
                thread.Dispose();
            }
            _threads.Clear();
        }
    }
}