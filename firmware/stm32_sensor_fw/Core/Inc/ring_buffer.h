/**
 * ring_buffer.h
 * Lock-free single-producer / single-consumer byte ring buffer.
 *
 * Producer: UART RX interrupt (writes head)
 * Consumer: main loop        (writes tail)
 * Because each index is written by only one side, no interrupt
 * disabling is needed on a Cortex-M (16-bit aligned writes are atomic).
 */
#ifndef RING_BUFFER_H
#define RING_BUFFER_H

#include <stdint.h>
#include <stdbool.h>

#define RB_SIZE 256u /* must be a power of 2 (index wrap uses a bit mask) */

typedef struct
{
    volatile uint8_t  buf[RB_SIZE];
    volatile uint16_t head;           /* next write position (ISR)       */
    volatile uint16_t tail;           /* next read position (main loop)  */
    volatile uint32_t overflow_count; /* bytes dropped because buffer full */
} ring_buffer_t;

void rb_init(ring_buffer_t *rb);
bool rb_push(ring_buffer_t *rb, uint8_t byte); /* call from ISR       */
bool rb_pop(ring_buffer_t *rb, uint8_t *byte); /* call from main loop */

#endif /* RING_BUFFER_H */
