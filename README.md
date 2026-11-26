# STM32 Peripheral Driver Validation & Smart Sensor Monitoring Framework

STM32 firmware that reads an **MPU6050** sensor over **I2C** and exposes it through a
**UART command protocol**, plus a **Python / pytest** framework that automatically validates
the firmware: protocol correctness, invalid inputs, boundary conditions, error recovery,
streaming timing and communication latency.

**Tech:** Embedded C · STM32CubeIDE / CubeMX · HAL · UART (interrupt-driven) · I2C · Python · pytest · Wokwi · Git

```
 ┌──────────── PC (Python / pytest) ────────────┐          ┌────────── STM32F103C8 ──────────┐
 │ test_protocol   test_invalid_inputs          │  UART    │ USART1 ISR ─► ring buffer (256) │
 │ test_boundaries test_error_recovery          │  9600    │ line assembler ─► protocol.c    │
 │ test_streaming  test_latency                 │◄────────►│ mpu6050.c (timeouts, retries,   │
 │        └── dut_client.py (pyserial)          │          │   bus recovery, fault inject)   │──I2C──► MPU6050
 │ reports: results.xml, latency_*.csv,         │          │ streaming + heartbeat LED       │
 │          regression_history.csv              │          │ (non-blocking, HAL_GetTick)     │
 └──────────────────────────────────────────────┘          └─────────────────────────────────┘
```

## Features

**Firmware (`firmware/stm32_sensor_fw/Core/`)**
- `app.c`: interrupt-driven UART RX (`HAL_UART_Receive_IT`) into a lock-free ring buffer, so nothing blocks waiting for input
- `ring_buffer.c`: single-producer/single-consumer buffer with an overflow counter. A line that lost bytes is rejected (`ERR,RX_OVERFLOW`) rather than executed.
- `protocol.c`: command parser with strict argument validation (see [docs/PROTOCOL.md](docs/PROTOCOL.md))
- `mpu6050.c`: I2C driver with:
  - HAL error → specific error code mapping (NACK / TIMEOUT / BUSY / BUS / wrong chip ID)
  - 10 ms per-transaction timeout, 3 retries, and automatic I2C peripheral reset after bus faults
  - lazy re-initialisation, so the driver recovers by itself once the fault is gone
  - **fault injection** (`FAULT,NACK|TIMEOUT`), so the tests can prove that the error paths work
- Non-blocking streaming mode (`RATE`, `STREAM`) and a heartbeat LED on PC13
- Integer-only maths: temperature in centi-degrees, so no float printf is needed on the MCU

**Validation framework (`host/`)**
| Test file | What it checks |
|---|---|
| `test_protocol.py` | every valid command returns a correctly formatted reply |
| `test_invalid_inputs.py` | unknown commands, bad/missing arguments, binary garbage, over-long lines, empty lines: the firmware must reply with an error and keep working |
| `test_boundaries.py` | values at / just inside / just outside limits, uint32 overflow, max line length, a burst of 20 back-to-back commands (ring buffer) |
| `test_error_recovery.py` | injected I2C NACK/TIMEOUT are reported correctly, error counters increase, UART stays responsive, the sensor recovers after the fault clears |
| `test_streaming.py` | DATA rate accuracy, sequence numbers without gaps, stop on command, commands still work while streaming |
| `test_latency.py` | 100-sample round-trip latency (min / avg / p95 / max) saved to CSV |

Each run appends a row to `reports/regression_history.csv` (date, firmware version, passed/failed/skipped), so you can compare firmware versions over time.

## How to run

### 1. Build the firmware
Open `firmware/stm32_sensor_fw` in STM32CubeIDE and build it (Debug). This produces `Debug/stm32_sensor_fw.elf`.

### 2a. Run in the simulator (no hardware)
1. Install the **Wokwi Simulator** extension in VS Code.
2. Select `firmware/stm32_sensor_fw/wokwi.toml` and press **F1 → Wokwi: Start Simulator**.
3. The UART is exposed at `rfc2217://localhost:4000`. The Wokwi serial monitor works at a fixed **9600 baud**, so USART1 is set to 9600 for simulation.

### 2b. Or run on real hardware
Flash the board with CubeIDE and connect a USB-UART adapter to PA9/PA10. Use its COM port in the commands below.

### 3. Run the tests
```bash
cd host
pip install -r requirements.txt
python dut_client.py rfc2217://localhost:4000             # quick manual check
python -m pytest --junitxml=../reports/results.xml         # simulator (default port)
python -m pytest --port=COM5 --baud=115200                # real hardware (same baud as CubeMX)
```

## Results
<!-- Add a screenshot of the pytest summary, the latency numbers and the Wokwi logic analyzer trace here -->

## Project structure
```
firmware/stm32_sensor_fw/   CubeMX + CubeIDE project (Core/Src: app, protocol, mpu6050, ring_buffer)
  ├── diagram.json          Wokwi circuit: Blue Pill + MPU6050 + logic analyzer
  └── wokwi.toml            Wokwi config (firmware path, RFC2217 port)
host/                       Python DUT client + pytest suite
docs/PROTOCOL.md            Command/response specification
reports/                    Generated test results (git-ignored)
```
