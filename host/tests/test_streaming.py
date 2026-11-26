"""Streaming mode: periodic DATA lines at the configured rate."""
import re
import time

DATA_RE = re.compile(r"DATA,(\d+),(TEMP,-?\d+|ERR,\w+)")


def collect_stream(dut, seconds):
    lines = []
    end = time.perf_counter() + seconds
    while time.perf_counter() < end:
        line = dut.read_line(timeout=0.05)
        if line and line.startswith("DATA,"):
            lines.append(line)
    return lines


def test_stream_on_off_replies(dut):
    assert dut.query("STREAM,ON") == "OK,STREAM,ON"
    assert dut.status()["STREAM"] == "ON"
    assert dut.query("STREAM,OFF") == "OK,STREAM,OFF"


def test_stream_rate_and_sequence(dut):
    dut.query("RATE,200")
    dut.query("STREAM,ON")
    lines = collect_stream(dut, 2.0)  # expect about 10 samples
    dut.query("STREAM,OFF")

    assert 7 <= len(lines) <= 13, f"got {len(lines)} samples in 2 s at 200 ms"
    seqs = []
    for line in lines:
        m = DATA_RE.fullmatch(line)
        assert m, line
        seqs.append(int(m.group(1)))
    assert all(b == a + 1 for a, b in zip(seqs, seqs[1:])), f"sequence gaps: {seqs}"


def test_stream_stops_when_off(dut):
    dut.query("RATE,100")
    dut.query("STREAM,ON")
    time.sleep(0.3)
    dut.query("STREAM,OFF")
    dut.drain(quiet_time=0.2)
    assert collect_stream(dut, 0.5) == []


def test_commands_work_while_streaming(dut):
    dut.query("RATE,100")
    dut.query("STREAM,ON")
    for _ in range(10):
        assert dut.query("PING") == "OK,PONG"  # DATA lines are filtered by the client
    dut.query("STREAM,OFF")
