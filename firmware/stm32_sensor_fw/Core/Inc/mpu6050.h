/**
 * mpu6050.h
 * Minimal MPU6050 (accelerometer + temperature) driver over I2C1 using HAL.
 *
 * Every function returns a sensor_status_t so the caller always knows
 * exactly what went wrong (NACK, timeout, busy bus, wrong chip ID ...).
 */
#ifndef MPU6050_H
#define MPU6050_H

#include <stdint.h>
#include <stdbool.h>

typedef enum
{
    SENSOR_OK = 0,
    SENSOR_ERR_NACK,    /* device did not acknowledge (missing / wrong address) */
    SENSOR_ERR_TIMEOUT, /* bus transaction did not finish in time               */
    SENSOR_ERR_BUSY,    /* bus stuck busy                                       */
    SENSOR_ERR_BUS,     /* other bus error (arbitration lost, bus error ...)    */
    SENSOR_ERR_ID       /* a device answered but it is not an MPU6050           */
} sensor_status_t;

/* Fault injection: lets the test framework force errors on purpose
 * to prove the error handling and recovery paths really work. */
typedef enum
{
    FAULT_NONE = 0,
    FAULT_NACK,
    FAULT_TIMEOUT
} fault_mode_t;

sensor_status_t mpu6050_init(void);
sensor_status_t mpu6050_read_temp_centi(int32_t *temp_c_x100);
sensor_status_t mpu6050_read_accel(int16_t *x, int16_t *y, int16_t *z);
void            mpu6050_recover_bus(void);

bool         mpu6050_is_ready(void);
uint32_t     mpu6050_error_count(void);
void         mpu6050_set_fault(fault_mode_t mode);
fault_mode_t mpu6050_get_fault(void);

const char *sensor_status_str(sensor_status_t status);

#endif /* MPU6050_H */
