"""Latency measurement: round-trip time for request -> reply.
Results are saved to reports/latency_<timestamp>.csv."""
import csv
import datetime
import statistics

import pytest

from conftest import REPORTS_DIR

SAMPLES = 100
# At 9600 baud one character takes ~1.04 ms, so a long reply like STATUS (~95 chars)
# needs ~100 ms just on the wire. Limit is generous for the simulator; tighten it
# (and use 115200 baud) on real hardware.
P95_LIMIT_MS = 300.0


def percentile(values, pct):
    ordered = sorted(values)
    index = max(0, int(round(pct / 100 * len(ordered))) - 1)
    return ordered[index]


@pytest.mark.latency
@pytest.mark.parametrize("cmd", ["PING", "STATUS", "READ,TEMP"])
def test_latency(dut, cmd):
    samples = []
    for _ in range(SAMPLES):
        reply, ms = dut.timed_query(cmd)
        assert reply.startswith(("OK,", "ERR,"))
        samples.append(ms)

    stats = {
        "min": min(samples),
        "avg": statistics.mean(samples),
        "p95": percentile(samples, 95),
        "max": max(samples),
    }
    print(f"\n{cmd}: " + "  ".join(f"{k}={v:.2f}ms" for k, v in stats.items()))

    REPORTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = cmd.replace(",", "_")
    with (REPORTS_DIR / f"latency_{safe}_{stamp}.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["sample", "latency_ms"])
        for i, v in enumerate(samples):
            w.writerow([i, f"{v:.3f}"])

    assert stats["p95"] < P95_LIMIT_MS
