import subprocess
import sys
import signal

def main():
    # Start Streamlit as a subprocess
    proc = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "webapp.py"])
    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nCaught Ctrl+C. Shutting down Streamlit…", flush=True)
        # Relay SIGINT to the subprocess (just in case)
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("Streamlit didn’t shut down in time. Killing it.")
                proc.kill()
        print("Exited cleanly.")


if __name__ == '__main__':
    main()
