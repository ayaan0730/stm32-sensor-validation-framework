/**
 * app.h
 * Application layer: glues UART (interrupt-driven RX), the command
 * protocol, the sensor driver, streaming and the heartbeat LED together.
 *
 * main.c only needs to call app_init() once and app_loop() forever.
 */
#ifndef APP_H
#define APP_H

#include <stdint.h>

void     app_init(void);
void     app_loop(void);

uint32_t app_rx_overflow_count(void);
uint32_t app_uart_error_count(void);

#endif /* APP_H */
