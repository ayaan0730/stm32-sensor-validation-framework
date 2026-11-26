/**
 * protocol.h
 * Text command protocol spoken over UART.
 *
 * Request : <CMD>[,<ARG>]\n         (max CMD_MAX_LEN characters, case-sensitive)
 * Reply   : OK,<...>\r\n  or  ERR,<CODE>\r\n
 * Stream  : DATA,<seq>,TEMP,<centi-degC>\r\n   (only while STREAM is ON)
 *
 * The parser is pure logic (no UART code here) so it is easy to read and test.
 */
#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#define FW_NAME       "stm32_sensor_fw"
#define FW_VERSION    "0.2.0"

#define CMD_MAX_LEN   64u   /* longest accepted command line (without \n) */
#define REPLY_MAX_LEN 128u

#define RATE_MIN_MS   100u
#define RATE_MAX_MS   10000u
#define RATE_DEFAULT_MS 1000u

typedef struct
{
    bool     stream_on;
    uint32_t stream_period_ms;
} app_config_t;

void protocol_handle_line(const char *line, char *reply, size_t reply_len, app_config_t *cfg);

#endif /* PROTOCOL_H */
