"""Negative tests: bad input must give a clear error, never a crash or hang."""
import pytest

BAD_COMMANDS = [
    ("XYZ", "ERR,UNKNOWN_CMD"),
    ("ping", "ERR,UNKNOWN_CMD"),          # commands are case-sensitive
    (" PING", "ERR,UNKNOWN_CMD"),         # leading space
    ("PING,1", "ERR,BAD_ARG"),            # PING takes no argument
    ("READ", "ERR,BAD_ARG"),              # missing argument
    ("READ,", "ERR,BAD_ARG"),             # empty argument
    ("READ,HUMIDITY", "ERR,BAD_ARG"),     # unsupported sensor channel
    ("RATE", "ERR,BAD_ARG"),
    ("RATE,abc", "ERR,BAD_ARG"),
    ("RATE,-5", "ERR,BAD_ARG"),
    ("RATE,1.5", "ERR,BAD_ARG"),
    ("RATE, 500", "ERR,BAD_ARG"),
    ("STREAM", "ERR,BAD_ARG"),
    ("STREAM,MAYBE", "ERR,BAD_ARG"),
    ("FAULT,EXPLODE", "ERR,BAD_ARG"),
    (",,,", "ERR,UNKNOWN_CMD"),
]


@pytest.mark.parametrize("cmd,expected", BAD_COMMANDS)
def test_bad_command_returns_error(dut, cmd, expected):
    assert dut.query(cmd) == expected
    assert dut.query("PING") == "OK,PONG", "firmware must still work after bad input"


def test_binary_garbage(dut):
    dut.send_raw(bytes([0xFF, 0xFE, 0x00, 0x80, 0x7F]) + b"\n")
    reply = dut.read_line()
    assert reply is not None and reply.startswith("ERR,")
    assert dut.query("PING") == "OK,PONG"


def test_empty_lines_are_ignored(dut):
    dut.send_raw(b"\n\n\r\n")
    assert dut.read_line(timeout=0.3) is None, "empty lines must not produce a reply"
    assert dut.query("PING") == "OK,PONG"


def test_line_too_long(dut):
    assert dut.query("A" * 200) == "ERR,TOO_LONG"
    assert dut.query("PING") == "OK,PONG"
