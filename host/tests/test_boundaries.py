"""Boundary tests: values exactly at, just inside and just outside the limits."""
import pytest

CMD_MAX_LEN = 64
RATE_MIN, RATE_MAX = 100, 10000


@pytest.mark.parametrize("value,expected", [
    (0, "ERR,RANGE"),
    (RATE_MIN - 1, "ERR,RANGE"),
    (RATE_MIN, f"OK,RATE,{RATE_MIN}"),
    (RATE_MIN + 1, f"OK,RATE,{RATE_MIN + 1}"),
    (RATE_MAX - 1, f"OK,RATE,{RATE_MAX - 1}"),
    (RATE_MAX, f"OK,RATE,{RATE_MAX}"),
    (RATE_MAX + 1, "ERR,RANGE"),
    (4294967296, "ERR,RANGE"),          # bigger than uint32 - must not wrap around
    (99999999999999999999, "ERR,RANGE"),
])
def test_rate_limits(dut, value, expected):
    assert dut.query(f"RATE,{value}") == expected


def test_rate_is_stored(dut):
    dut.query("RATE,250")
    assert dut.status()["RATE"] == "250"


def test_command_exactly_max_length_is_parsed(dut):
    line = "X" * CMD_MAX_LEN
    assert dut.query(line) == "ERR,UNKNOWN_CMD"  # parsed normally, just unknown


def test_command_one_over_max_length(dut):
    line = "X" * (CMD_MAX_LEN + 1)
    assert dut.query(line) == "ERR,TOO_LONG"


def test_burst_of_back_to_back_commands(dut):
    """Send 20 commands without waiting - tests the interrupt RX ring buffer."""
    n = 20
    dut.send_raw(b"PING\n" * n)
    replies = [dut.read_line(timeout=2.0) for _ in range(n)]
    assert replies == ["OK,PONG"] * n
    assert dut.status()["RX_OVF"] == "0", "no bytes may be dropped"
