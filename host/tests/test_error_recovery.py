"""Error handling & recovery: force I2C faults and check the firmware
reports them correctly and works again afterwards."""
import pytest


@pytest.mark.parametrize("fault,expected", [
    ("NACK", "ERR,I2C_NACK"),
    ("TIMEOUT", "ERR,I2C_TIMEOUT"),
])
@pytest.mark.parametrize("channel", ["TEMP", "ACCEL"])
def test_injected_fault_is_reported(dut, fault, expected, channel):
    assert dut.query(f"FAULT,{fault}") == f"OK,FAULT,{fault}"
    assert dut.query(f"READ,{channel}") == expected


def test_error_counter_increments(dut):
    before = int(dut.status()["I2C_ERR"])
    dut.query("FAULT,NACK")
    dut.query("READ,TEMP")
    dut.query("READ,TEMP")
    after = int(dut.status()["I2C_ERR"])
    assert after >= before + 2


def test_uart_still_responsive_during_sensor_fault(dut):
    dut.query("FAULT,TIMEOUT")
    for _ in range(5):
        assert dut.query("READ,TEMP") == "ERR,I2C_TIMEOUT"
        assert dut.query("PING") == "OK,PONG"


@pytest.mark.sensor
def test_recovers_after_fault_cleared(dut, sensor_ok):
    dut.query("FAULT,TIMEOUT")
    assert dut.query("READ,TEMP") == "ERR,I2C_TIMEOUT"
    dut.query("FAULT,NONE")
    assert dut.query("READ,TEMP").startswith("OK,TEMP,")
    assert dut.status()["SENSOR"] == "OK"


@pytest.mark.sensor
def test_manual_bus_reset(dut, sensor_ok):
    assert dut.query("I2C_RESET") == "OK,I2C_RESET"
    assert dut.query("READ,TEMP").startswith("OK,TEMP,")


def test_streaming_reports_errors_during_fault(dut):
    dut.query("FAULT,NACK")
    dut.query("RATE,100")
    dut.query("STREAM,ON")
    line = dut.read_line(timeout=1.0)
    dut.query("STREAM,OFF")
    assert line is not None and line.startswith("DATA,")
    assert line.endswith(",ERR,I2C_NACK")
