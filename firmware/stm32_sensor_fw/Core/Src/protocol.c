/**
 * protocol.c
 * Command parser / dispatcher. See protocol.h and docs/PROTOCOL.md.
 */
#include "protocol.h"
#include "app.h"
#include "mpu6050.h"
#include "main.h" /* HAL_GetTick() */

#include <stdio.h>
#include <string.h>

/* Strict unsigned decimal parser: digits only, no sign, no spaces.
 * Very large values saturate (so they are reported as out of RANGE,
 * not silently wrapped around). */
static bool parse_uint(const char *s, uint32_t *out)
{
    uint32_t value = 0u;

    if ((s == NULL) || (*s == '\0')) { return false; }

    for (const char *p = s; *p != '\0'; p++)
    {
        if ((*p < '0') || (*p > '9')) { return false; }
        if (value < 1000000u)
        {
            value = (value * 10u) + (uint32_t)(*p - '0');
        }
    }
    *out = value;
    return true;
}

static void reply_sensor_error(char *reply, size_t n, sensor_status_t st)
{
    snprintf(reply, n, "ERR,%s", sensor_status_str(st));
}

void protocol_handle_line(const char *line, char *reply, size_t n, app_config_t *cfg)
{
    char  buf[CMD_MAX_LEN + 1u];
    char *cmd;
    char *arg;

    /* Work on a local copy so we can split it */
    strncpy(buf, line, CMD_MAX_LEN);
    buf[CMD_MAX_LEN] = '\0';

    cmd = buf;
    arg = strchr(buf, ',');
    if (arg != NULL)
    {
        *arg = '\0'; /* terminate the command name */
        arg++;       /* argument starts after the comma */
    }

    /* ---------------- PING ---------------- */
    if (strcmp(cmd, "PING") == 0)
    {
        if (arg != NULL) { snprintf(reply, n, "ERR,BAD_ARG"); return; }
        snprintf(reply, n, "OK,PONG");
    }
    /* ---------------- VERSION ------------- */
    else if (strcmp(cmd, "VERSION") == 0)
    {
        if (arg != NULL) { snprintf(reply, n, "ERR,BAD_ARG"); return; }
        snprintf(reply, n, "OK,VERSION,%s,%s", FW_NAME, FW_VERSION);
    }
    /* ---------------- STATUS -------------- */
    else if (strcmp(cmd, "STATUS") == 0)
    {
        if (arg != NULL) { snprintf(reply, n, "ERR,BAD_ARG"); return; }
        snprintf(reply, n,
                 "OK,STATUS,SENSOR=%s,UPTIME=%lu,RX_OVF=%lu,UART_ERR=%lu,I2C_ERR=%lu,STREAM=%s,RATE=%lu",
                 mpu6050_is_ready() ? "OK" : "ERR",
                 (unsigned long)HAL_GetTick(),
                 (unsigned long)app_rx_overflow_count(),
                 (unsigned long)app_uart_error_count(),
                 (unsigned long)mpu6050_error_count(),
                 cfg->stream_on ? "ON" : "OFF",
                 (unsigned long)cfg->stream_period_ms);
    }
    /* ---------------- READ,<TEMP|ACCEL> --- */
    else if (strcmp(cmd, "READ") == 0)
    {
        if (arg == NULL) { snprintf(reply, n, "ERR,BAD_ARG"); return; }

        if (strcmp(arg, "TEMP") == 0)
        {
            int32_t t;
            sensor_status_t st = mpu6050_read_temp_centi(&t);
            if (st != SENSOR_OK) { reply_sensor_error(reply, n, st); return; }
            snprintf(reply, n, "OK,TEMP,%ld", (long)t);
        }
        else if (strcmp(arg, "ACCEL") == 0)
        {
            int16_t x, y, z;
            sensor_status_t st = mpu6050_read_accel(&x, &y, &z);
            if (st != SENSOR_OK) { reply_sensor_error(reply, n, st); return; }
            snprintf(reply, n, "OK,ACCEL,%d,%d,%d", (int)x, (int)y, (int)z);
        }
        else
        {
            snprintf(reply, n, "ERR,BAD_ARG");
        }
    }
    /* ---------------- RATE,<ms> ----------- */
    else if (strcmp(cmd, "RATE") == 0)
    {
        uint32_t ms;
        if (!parse_uint(arg, &ms)) { snprintf(reply, n, "ERR,BAD_ARG"); return; }
        if ((ms < RATE_MIN_MS) || (ms > RATE_MAX_MS)) { snprintf(reply, n, "ERR,RANGE"); return; }
        cfg->stream_period_ms = ms;
        snprintf(reply, n, "OK,RATE,%lu", (unsigned long)ms);
    }
    /* ---------------- STREAM,<ON|OFF> ----- */
    else if (strcmp(cmd, "STREAM") == 0)
    {
        if ((arg != NULL) && (strcmp(arg, "ON") == 0))
        {
            cfg->stream_on = true;
            snprintf(reply, n, "OK,STREAM,ON");
        }
        else if ((arg != NULL) && (strcmp(arg, "OFF") == 0))
        {
            cfg->stream_on = false;
            snprintf(reply, n, "OK,STREAM,OFF");
        }
        else
        {
            snprintf(reply, n, "ERR,BAD_ARG");
        }
    }
    /* ---------------- FAULT,<NONE|NACK|TIMEOUT> (test hook) */
    else if (strcmp(cmd, "FAULT") == 0)
    {
        if      ((arg != NULL) && (strcmp(arg, "NONE") == 0))    { mpu6050_set_fault(FAULT_NONE); }
        else if ((arg != NULL) && (strcmp(arg, "NACK") == 0))    { mpu6050_set_fault(FAULT_NACK); }
        else if ((arg != NULL) && (strcmp(arg, "TIMEOUT") == 0)) { mpu6050_set_fault(FAULT_TIMEOUT); }
        else { snprintf(reply, n, "ERR,BAD_ARG"); return; }
        snprintf(reply, n, "OK,FAULT,%s", arg);
    }
    /* ---------------- I2C_RESET ----------- */
    else if (strcmp(cmd, "I2C_RESET") == 0)
    {
        sensor_status_t st;
        if (arg != NULL) { snprintf(reply, n, "ERR,BAD_ARG"); return; }
        mpu6050_recover_bus();
        st = mpu6050_init();
        if (st != SENSOR_OK) { reply_sensor_error(reply, n, st); return; }
        snprintf(reply, n, "OK,I2C_RESET");
    }
    /* ---------------- anything else ------- */
    else
    {
        snprintf(reply, n, "ERR,UNKNOWN_CMD");
    }
}
