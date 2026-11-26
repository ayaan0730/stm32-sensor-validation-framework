"""
Shared pytest setup:
  * --port option (simulator or real board)
  * one serial connection for the whole test session
  * device is put back into a clean state before every test
  * a row is appended to reports/regression_history.csv after every run
"""
import csv
import datetime
import os
from pathlib import Path

import pytest

from dut_client import DutClient

REPORTS_DIR = Path(__file__).resolve().parents[2] / "reports"
DEFAULT_PORT = os.environ.get("DUT_PORT", "rfc2217://localhost:4000")
DEFAULT_BAUD = int(os.environ.get("DUT_BAUD", "9600"))  # Wokwi serial monitor is fixed at 9600

_run_info = {"firmware": "unknown", "port": DEFAULT_PORT}


def pytest_addoption(parser):
    parser.addoption("--port", default=DEFAULT_PORT,
                     help="Serial port of the DUT, e.g. rfc2217://localhost:4000 or COM5")
    parser.addoption("--baud", type=int, default=DEFAULT_BAUD,
                     help="UART baud rate (must match the firmware), default 9600")


@pytest.fixture(scope="session")
def dut(request):
    port = request.config.getoption("--port")
    _run_info["port"] = port
    try:
        client = DutClient(port, baudrate=request.config.getoption("--baud"))
    except Exception as exc:  # noqa: BLE001
        pytest.exit(f"Cannot open {port}: {exc}\nIs the Wokwi simulator running?", returncode=2)

    client.drain()
    reply = client.query("PING")
    if reply != "OK,PONG":
        pytest.exit(f"DUT not responding correctly to PING (got {reply!r})", returncode=2)
    _run_info["firmware"] = client.query("VERSION").split(",")[-1]  # e.g. 0.2.0
    yield client
    client.query("STREAM,OFF")
    client.query("FAULT,NONE")
    client.close()


@pytest.fixture(autouse=True)
def clean_state(dut):
    """Every test starts with: no streaming, no injected fault, default rate."""
    dut.query("STREAM,OFF")
    dut.drain(quiet_time=0.1)
    dut.query("FAULT,NONE")
    dut.query("RATE,1000")
    dut.stream_lines.clear()
    yield


@pytest.fixture
def sensor_ok(dut):
    """Skip the test if the MPU6050 is not answering (e.g. not wired in the simulator)."""
    if not dut.query("READ,TEMP").startswith("OK,TEMP,"):
        pytest.skip("MPU6050 sensor not available")


def pytest_sessionfinish(session, exitstatus):
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is None:
        return
    counts = {k: len(reporter.stats.get(k, [])) for k in ("passed", "failed", "skipped", "error")}
    REPORTS_DIR.mkdir(exist_ok=True)
    history = REPORTS_DIR / "regression_history.csv"
    new_file = not history.exists()
    with history.open("a", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["timestamp", "firmware", "port", "passed", "failed", "skipped", "errors"])
        writer.writerow([
            datetime.datetime.now().isoformat(timespec="seconds"),
            _run_info["firmware"], _run_info["port"],
            counts["passed"], counts["failed"], counts["skipped"], counts["error"],
        ])
