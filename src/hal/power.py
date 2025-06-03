#!/usr/bin/env python3
from periphery import PWM
import time

# Servo Configuration (adjust these!)
PWM_CHIP = 1          # Try 0 or 1 (check `/sys/class/pwm/`)
PWM_CHANNEL = 0        # Channel number (usually 0)
FREQUENCY = 50         # 50Hz for servos
MIN_PULSE_MS = 1.0     # Pulse width for 0° (ms)
MAX_PULSE_MS = 2.0     # Pulse width for 180° (ms)

def set_servo_angle(pwm, angle):
    """Rotate servo to a specific angle (0-180°)."""
    # Clamp angle between 0 and 180
    angle = max(0, min(180, angle))
    
    # Calculate duty cycle (e.g., 1ms=0°, 2ms=180°)
    pulse_width_ms = MIN_PULSE_MS + (angle / 180) * (MAX_PULSE_MS - MIN_PULSE_MS)
    duty_cycle = (pulse_width_ms / (1000 / FREQUENCY))  # Convert ms to duty cycle
    
    # Apply to PWM
    pwm.duty_cycle = duty_cycle
    print(f"Angle: {angle}° → Duty: {duty_cycle:.3f}")

# Initialize PWM
try:
    pwm = PWM(PWM_CHIP, PWM_CHANNEL)
    pwm.frequency = FREQUENCY
    pwm.enable()

    # Example: Rotate to 90°
    set_servo_angle(pwm, 90)
    time.sleep(1)
    set_servo_angle(pwm, 0)
    time.sleep(1)

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'pwm' in locals():
        pwm.close()
