# UART Command Protocol

**Link:** USART1, 9600 baud in the Wokwi simulator (its serial monitor is fixed at 9600), 115200 recommended on real hardware, 8N1 (PA9 = TX, PA10 = RX)
**Format:** ASCII lines. Commands end with `\n` (`\r\n` also accepted). Replies end with `\r\n`.
**Rules:** commands are case-sensitive, max **64** characters, and empty lines are ignored.

| Command | Reply (success) | Possible errors |
|---|---|---|
| `PING` | `OK,PONG` | `BAD_ARG` |
| `VERSION` | `OK,VERSION,stm32_sensor_fw,0.2.0` | `BAD_ARG` |
| `STATUS` | `OK,STATUS,SENSOR=OK,UPTIME=1234,RX_OVF=0,UART_ERR=0,I2C_ERR=0,STREAM=OFF,RATE=1000` | `BAD_ARG` |
| `READ,TEMP` | `OK,TEMP,2531` (= 25.31 °C, centi-degrees) | `BAD_ARG`, `I2C_*`, `SENSOR_ID` |
| `READ,ACCEL` | `OK,ACCEL,<x>,<y>,<z>` (raw 16-bit) | `BAD_ARG`, `I2C_*`, `SENSOR_ID` |
| `RATE,<ms>` | `OK,RATE,<ms>` (100–10000) | `BAD_ARG`, `RANGE` |
| `STREAM,ON` / `STREAM,OFF` | `OK,STREAM,ON` / `OK,STREAM,OFF` | `BAD_ARG` |
| `FAULT,NONE\|NACK\|TIMEOUT` | `OK,FAULT,<mode>` (test hook: forces I2C errors) | `BAD_ARG` |
| `I2C_RESET` | `OK,I2C_RESET` (re-initialises bus and sensor) | `I2C_*`, `SENSOR_ID` |

**Streaming:** when it's ON, the device sends `DATA,<seq>,TEMP,<centi-degC>` (or `DATA,<seq>,ERR,<code>`) every `RATE` ms.
**Boot banner:** `BOOT,stm32_sensor_fw,<version>,SENSOR=<status>`

## Error codes (`ERR,<code>`)

| Code | Meaning |
|---|---|
| `UNKNOWN_CMD` | command name not recognised |
| `BAD_ARG` | missing, extra or malformed argument |
| `RANGE` | number outside the allowed range |
| `TOO_LONG` | line longer than 64 characters |
| `RX_OVERFLOW` | bytes were lost in the RX ring buffer, so the damaged line was not executed |
| `I2C_NACK` | sensor did not acknowledge |
| `I2C_TIMEOUT` | I2C transaction timed out (the bus is reset automatically) |
| `I2C_BUSY` / `I2C_BUS` | bus stuck or bus error (the bus is reset automatically) |
| `SENSOR_ID` | a device answered, but WHO_AM_I ≠ 0x68 |
