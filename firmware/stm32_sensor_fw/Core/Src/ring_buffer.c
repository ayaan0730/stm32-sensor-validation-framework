/**
 * ring_buffer.c
 * See ring_buffer.h for the design notes.
 */
#include "ring_buffer.h"

void rb_init(ring_buffer_t *rb)
{
    rb->head = 0u;
    rb->tail = 0u;
    rb->overflow_count = 0u;
}

bool rb_push(ring_buffer_t *rb, uint8_t byte)
{
    uint16_t next = (uint16_t)((rb->head + 1u) & (RB_SIZE - 1u));

    if (next == rb->tail)
    {
        /* Buffer full: drop the byte and count it, never block in an ISR */
        rb->overflow_count++;
        return false;
    }

    rb->buf[rb->head] = byte;
    rb->head = next; /* publish only after the data is written */
    return true;
}

bool rb_pop(ring_buffer_t *rb, uint8_t *byte)
{
    if (rb->tail == rb->head)
    {
        return false; /* empty */
    }

    *byte = rb->buf[rb->tail];
    rb->tail = (uint16_t)((rb->tail + 1u) & (RB_SIZE - 1u));
    return true;
}
