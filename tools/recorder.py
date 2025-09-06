import argparse
from .recorder.main_recorder import Recorder

recorder_instance = None

def start_recording(whitelist=None, output_folder="recorder/output"):
    """
    Starts a new recording session.
    """
    global recorder_instance
    if recorder_instance and recorder_instance.is_recording:
        return "Recording is already in progress."

    recorder_instance = Recorder(output_folder=output_folder, whitelist=whitelist)
    recorder_instance.start()
    return "Recording started."

def stop_recording():
    """
    Stops the current recording session.
    """
    global recorder_instance
    if not recorder_instance or not recorder_instance.is_recording:
        return "No active recording session found."

    recorder_instance.stop()
    return "Recording stopped."

def main():
    """
    Original main function with hotkey support for local execution.
    """
    from pynput import keyboard

    parser = argparse.ArgumentParser(description="Record UI interactions.")
    parser.add_argument('-wh', '--whitelist', type=str, nargs='+', help='Filter recording by process name(s).')
    args = parser.parse_args()

    def on_activate_record():
        global recorder_instance
        if not recorder_instance:
            recorder_instance = Recorder(whitelist=args.whitelist)

        if recorder_instance.is_recording:
            stop_recording()
        else:
            start_recording(whitelist=args.whitelist)

    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<alt>+<shift>+r'),
        on_activate_record)

    def on_press(key):
        hotkey.press(listener.canonical(key))

    def on_release(key):
        hotkey.release(listener.canonical(key))
        if key == keyboard.Key.esc:
            if recorder_instance and recorder_instance.is_recording:
                stop_recording()
            return False

    print("[Main] Press Alt+Shift+R to start/stop recording. Press Esc to exit.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        print("[Main] Hotkey listener started.")
        listener.join()
    print("[Main] Exiting script.")

if __name__ == "__main__":
    main()
