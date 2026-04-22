"""
motion_helpers.py

Helper functions for Subteam 2 driving code.

Why this file exists:
- Keep small reusable motion-related functions in one place
- Make drive_controller.py easier to read
- Give the team a place to add motion logic later
"""


def clamp_value(value, minimum, maximum):
    """
    Keep a value inside a safe range.

    Example:
    If value = 2.0, minimum = -1.0, maximum = 1.0
    then this function returns 1.0

    In simple terms:
    "Do not let a speed go above or below allowed limits."
    """
    return max(minimum, min(value, maximum))


def is_stop_command(linear_x, angular_z, tolerance=1e-3):
    """
    Check if a command is basically telling the robot to stop.

    We use a tiny tolerance because sometimes numbers are very close to zero
    but not exactly zero.

    Returns:
    - True if both values are close to zero
    - False otherwise
    """
    return abs(linear_x) < tolerance and abs(angular_z) < tolerance


def format_motion_command(linear_x, angular_z):
    """
    Create a clean readable string for logging.

    This helps keep print/log messages consistent.
    """
    return f'linear.x: {linear_x:.2f}, angular.z: {angular_z:.2f}'
