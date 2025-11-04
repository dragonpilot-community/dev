"""
Copyright (c) 2025, Rick Lan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, and/or sublicense,
for non-commercial purposes only, subject to the following conditions:

- The above copyright notice and this permission notice shall be included in
  all copies or substantial portions of the Software.
- Commercial use (e.g. use in a product, service, or activity intended to
  generate revenue) is prohibited without explicit written permission from
  the copyright holder.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# --- DTSC (Dynamic Turn Speed Control) ---
#
# This module limits the model's planned speed (`v_pred`) based on
# predicted curvature (`predicted_yaw_rate`) to ensure safe cornering.
#
# It calculates the max safe speed for each point in the future plan
# and overrides `v_pred` if it's found to be too aggressive.
#
# --- Tuning ---
#
# 1. grip_level
#    Your main "aggression" knob.
#    - Too slow in turns? Increase this (e.g., 0.9 -> 0.95).
#    - Unsafe/scary in turns? Decrease this (e.g., 0.9 -> 0.85).
#
# 2. V_SAFETY_MARGIN_CURVE:
#    The "buffer" (in m/s) subtracted from the max speed.
#    - Too slow? Decrease these numbers.
#    - Too fast? Increase these numbers.
#
# 3. BASE_LAT_ACCEL_CURVE:
#    The core physics model of your car's grip (in m/s^2).
#    - Only touch this if `grip_level=1.0` is still too slow/fast.
#
# -----------------------------------------------------------------

import numpy as np

# --- Constants ---
# these should have the same array length
SPEED_POINTS = [5.0, 15.0, 25.0]         # m/s
BASE_LAT_ACCEL_CURVE = [1.5, 2.5, 3.5]  # m/s^2
V_SAFETY_MARGIN_CURVE = [0.8, 1.5, 2.2]  # m/s

# --- Hysteresis ---
# Frames to wait before activating / deactivating
ACTIVATION_FRAMES = 5
DEACTIVATION_FRAMES = 10


class DTSC:
  def __init__(self, grip_level=0.9):
    self.grip_level = grip_level
    self.active = False

    # Counters for hysteresis
    self.activation_counter = 0
    self.deactivation_counter = 0

    # Pre-calculate the grip-scaled curve
    self.scaled_lat_accel_curve = [x * self.grip_level for x in BASE_LAT_ACCEL_CURVE]

  def get_v_limited(self, enabled: bool, v_pred: np.array, yaw_rate_pred: float):
    """
    Limits predicted velocity array based on predicted curvature.
    """

    # Check if a limit is needed *at all* for this frame
    should_activate = False
    if enabled:
      # Calculate max_lat_accel and margin as ARRAYS based on v_pred (How much G-force is safe?)
      max_lat_accel_array = np.interp(v_pred, SPEED_POINTS, self.scaled_lat_accel_curve)
      # (How much speed should we subtract?)
      v_safety_margin_array = np.interp(v_pred, SPEED_POINTS, V_SAFETY_MARGIN_CURVE)

      # Calculate predicted curvature
      curvature_pred = yaw_rate_pred / np.clip(v_pred, 0.3, 100.0)

      # Calculate max speed for that curvature
      v_max_curvature = np.sqrt(max_lat_accel_array / (np.abs(curvature_pred) + 1e-3))

      # Apply safety margin and clip
      v_max = np.clip(v_max_curvature - v_safety_margin_array, 0.0, 100.0)

      # Limit the planned speed
      v_limited = np.minimum(v_pred, v_max)

      # Check if we *should* be active
      should_activate = np.any(v_limited < v_pred)

    else:
      # Not enabled, just return the original plan
      v_limited = v_pred
      should_activate = False

    if should_activate:
      self.deactivation_counter = 0
      self.activation_counter = min(self.activation_counter + 1, ACTIVATION_FRAMES)
      if self.activation_counter == ACTIVATION_FRAMES:
        self.active = True
    else:
      self.activation_counter = 0
      self.deactivation_counter = min(self.deactivation_counter + 1, DEACTIVATION_FRAMES)
      if self.deactivation_counter == DEACTIVATION_FRAMES:
        self.active = False

    # Only return the limited speeds if we are *actually* active
    return v_limited if self.active else v_pred
