"""Functional tests: every valid command gives a correctly formatted reply."""
import re

import pytest


def test_ping(dut):
    assert dut.query("PING") == "OK,PONG"


def test_version_format(dut):
    assert re.fullmatch(r"OK,VERSION,stm32_sensor_fw,\d+\.\d+\.\d+", dut.query("VERSION"))


def test_status_has_all_fields(dut):
    status = dut.status()
    for key in ("SENSOR", "UPTIME", "RX_OVF", "UART_ERR", "I2C_ERR", "STREAM", "RATE"):
        assert key in status, f"missing {key}"
    assert status["SENSOR"] in ("OK", "ERR")
    assert status["STREAM"] == "OFF"


def test_uptime_increases(dut):
    t1 = int(dut.status()["UPTIME"])
    t2 = int(dut.status()["UPTIME"])
    assert t2 >= t1


def test_crlf_line_ending_accepted(dut):
    dut.send_raw(b"PING\r\n")
    assert dut.read_line() == "OK,PONG"


@pytest.mark.sensor
def test_read_temp_format_and_range(dut, sensor_ok):
    reply = dut.query("READ,TEMP")
    m = re.fullmatch(r"OK,TEMP,(-?\d+)", reply)
    assert m, reply
    temp_c = int(m.group(1)) / 100
    assert -40.0 <= temp_c <= 85.0  # MPU6050 operating range


@pytest.mark.sensor
def test_read_accel_format(dut, sensor_ok):
    reply = dut.query("READ,ACCEL")
    m = re.fullmatch(r"OK,ACCEL,(-?\d+),(-?\d+),(-?\d+)", reply)
    assert m, reply
    for v in m.groups():
        assert -32768 <= int(v) <= 32767


def test_many_sequential_pings(dut):
    for _ in range(50):
        assert dut.query("PING") == "OK,PONG"
