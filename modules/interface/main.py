import subprocess

class StreamlitRunner:
    def __init__(self, app_path="app.py", port=8501):
        self.app_path = app_path
        self.port = port
        self.proc = None

    def start(self):
        if self.proc is None:
            self.proc = subprocess.Popen(
                ["streamlit", "run", self.app_path, f"--server.port={self.port}"]
            )
            print(f"Streamlit started on port {self.port}")
        else:
            print("Streamlit is already running.")

    def stop(self):
        if self.proc is not None:
            self.proc.terminate()
            self.proc.wait()
            print("Streamlit stopped.")
            self.proc = None
        else:
            print("Streamlit is not running.")

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None


if __name__ == "__main__":
    runner = StreamlitRunner(app_path="app.py", port=8501)
    runner.start()
    runner.stop()
