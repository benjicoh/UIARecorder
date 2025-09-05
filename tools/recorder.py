import argparse
from recorder.main_recorder import Recorder
from pynput import keyboard

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Record UI interactions.")
    parser.add_argument('-wh', '--whitelist', type=str, nargs='+', help='Filter recording by process name(s).')
    args = parser.parse_args()

    recorder = Recorder(whitelist=args.whitelist)

    def on_activate_record():
        if recorder.is_recording:
            recorder.stop()
        else:
            recorder.start()

    hotkey = keyboard.HotKey(
        keyboard.HotKey.parse('<alt>+<shift>+r'),
        on_activate_record)

    def on_press(key):
        hotkey.press(listener.canonical(key))

    def on_release(key):
        hotkey.release(listener.canonical(key))
        if key == keyboard.Key.esc:
            if recorder.is_recording:
                recorder.stop()
            return False

    print("[Main] Press Alt+Shift+R to start/stop recording. Press Esc to exit.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        print("[Main] Hotkey listener started.")
        listener.join()
    print("[Main] Exiting script.")
