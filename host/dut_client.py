"""
dut_client.py - talks to the STM32 firmware (the "DUT" = Device Under Test).

Works with:
  * Wokwi simulator : port = "rfc2217://localhost:4000"
  * Real hardware   : port = "COM5" (Windows) or "/dev/ttyUSB0" (Linux)
"""
import time

import serial


class DutClient:
    def __init__(self, port: str, baudrate: int = 9600, timeout: float = 1.0):
        self.port = port
        self.ser = serial.serial_for_url(port, baudrate=baudrate, timeout=0.05)
        self.default_timeout = timeout
        self._rx = b""
        self.stream_lines = []  # DATA,... lines received while waiting for a reply

    def close(self):
        self.ser.close()

    # ------------------------------------------------------------------ low level
    def send_raw(self, data: bytes):
        self.ser.write(data)
        self.ser.flush()

    def send_line(self, text: str):
        self.send_raw(text.encode("latin-1") + b"\n")

    def read_line(self, timeout: float = None):
        """Return one line (without \\r\\n) or None on timeout."""
        timeout = self.default_timeout if timeout is None else timeout
        deadline = time.perf_counter() + timeout
        while True:
            if b"\n" in self._rx:
                line, self._rx = self._rx.split(b"\n", 1)
                return line.rstrip(b"\r").decode("latin-1")
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return None
            chunk = self.ser.read(self.ser.in_waiting or 1)
            if chunk:
                self._rx += chunk

    def drain(self, quiet_time: float = 0.3):
        """Throw away everything the device sends until it is quiet."""
        while self.read_line(timeout=quiet_time) is not None:
            pass

    # ------------------------------------------------------------------ high level
    def query(self, cmd: str, timeout: float = None) -> str:
        """Send a command and return its reply (OK,... / ERR,...).
        Streaming DATA lines and BOOT banners are skipped and stored."""
        reply, _ = self.timed_query(cmd, timeout)
        return reply

    def timed_query(self, cmd: str, timeout: float = None):
        """Like query(), but also returns round-trip latency in milliseconds."""
        start = time.perf_counter()
        self.send_line(cmd)
        while True:
            line = self.read_line(timeout)
            if line is None:
                raise TimeoutError(f"No reply to {cmd!r} within timeout")
            if line.startswith("DATA,"):
                self.stream_lines.append(line)
                continue
            if line.startswith("BOOT,"):
                continue
            latency_ms = (time.perf_counter() - start) * 1000.0
            return line, latency_ms

    def status(self) -> dict:
        """Parse 'OK,STATUS,KEY=VAL,...' into a dict."""
        reply = self.query("STATUS")
        if not reply.startswith("OK,STATUS,"):
            raise RuntimeError(f"Bad STATUS reply: {reply!r}")
        fields = reply[len("OK,STATUS,"):].split(",")
        return dict(f.split("=", 1) for f in fields)


if __name__ == "__main__":
    # Quick manual check:  python dut_client.py rfc2217://localhost:4000 [baud]
    import sys

    port = sys.argv[1] if len(sys.argv) > 1 else "rfc2217://localhost:4000"
    baud = int(sys.argv[2]) if len(sys.argv) > 2 else 9600
    dut = DutClient(port, baudrate=baud)
    dut.drain()
    for cmd in ["PING", "VERSION", "STATUS", "READ,TEMP", "READ,ACCEL"]:
        reply, ms = dut.timed_query(cmd)
        print(f"{cmd:<12} -> {reply}   ({ms:.1f} ms)")
    dut.close()
