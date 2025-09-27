using System;
using System.Collections.Concurrent;
using System.Threading;

namespace Recorder.Utils
{
    public class DedicatedThread : IDisposable
    {
        private readonly Thread _thread;
        private readonly BlockingCollection<Action> _actionQueue = new BlockingCollection<Action>();
        private readonly CancellationTokenSource _cancellationTokenSource = new CancellationTokenSource();

        public DedicatedThread(bool isSta = false)
        {
            _thread = new Thread(() => ThreadLoop(_cancellationTokenSource.Token));
            if (isSta)
            {
                _thread.SetApartmentState(ApartmentState.STA);
            }
        }

        public void Start()
        {
            _thread.Start();
        }

        public void Stop()
        {
            _cancellationTokenSource.Cancel();
            _actionQueue.CompleteAdding();
            _thread.Join();
        }

        public void EnqueueAction(Action action)
        {
            if (!_actionQueue.IsAddingCompleted)
            {
                _actionQueue.Add(action);
            }
        }

        private void ThreadLoop(CancellationToken token)
        {
            while (!token.IsCancellationRequested)
            {
                try
                {
                    var action = _actionQueue.Take(token);
                    action?.Invoke();
                }
                catch (OperationCanceledException)
                {
                    // Expected when stopping
                    break;
                }
                catch (Exception ex)
                {
                    // Log the exception
                    Console.WriteLine($"Error on dedicated thread: {ex.Message}");
                }
            }
        }

        public void Dispose()
        {
            Stop();
            _actionQueue.Dispose();
            _cancellationTokenSource.Dispose();
        }
    }
}