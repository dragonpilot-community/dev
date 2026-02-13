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

import time
import numpy as np
from openpilot.selfdrive.modeld.constants import ModelConstants

# Cooldown times (how long to stay in experimental mode after trigger)
AEM_COOLDOWN_STOP = 0.5      # seconds - for stop sign/light detection
AEM_COOLDOWN_TTC = 2.0       # seconds - for lead TTC events

# Stop sign/light detection thresholds
SLOW_DOWN_BP = [0., 2.78, 5.56, 8.34, 11.12, 13.89, 15.28]
SLOW_DOWN_DIST = [10, 30., 50., 70., 80., 90., 120.]

# TTC-based triggering thresholds
TTC_THRESHOLD = 1.8          # seconds - trigger when TTC drops below this
MIN_SPEED_FOR_TTC = 5.0      # m/s (~18 km/h) - TTC meaningless at low speeds
MIN_CLOSING_SPEED = 0.5      # m/s - must be closing at least this fast

# Green light resume thresholds
STANDSTILL_THRESHOLD = 0.1   # m/s - considered stopped below this
GREEN_LIGHT_X_THRESHOLD = 30 # meters - model path must extend beyond this
GREEN_LIGHT_FRAMES = 5       # consecutive frames model must show clear path


class AEM:

  def __init__(self):
    self._active = False
    self._cooldown_end_time = 0.0
    self._green_light_counter = 0

  def _perform_experimental_mode(self, cooldown: float = AEM_COOLDOWN_TTC):
    self._active = True
    # Extend cooldown if new trigger comes in
    new_end = time.monotonic() + cooldown
    self._cooldown_end_time = max(self._cooldown_end_time, new_end)

  def get_mode(self, mode):
    # override mode
    if time.monotonic() < self._cooldown_end_time:
      mode = 'blended'
    else:
      self._active = False
    return mode

  def update_states(self, model_msg, radar_msg, v_ego):
    # Stop sign/light detection - model predicts stopping ahead
    # Uses max() so it can't shorten an existing longer cooldown
    if len(model_msg.orientation.x) == len(model_msg.position.x) == ModelConstants.IDX_N and \
      model_msg.position.x[ModelConstants.IDX_N - 1] < np.interp(v_ego, SLOW_DOWN_BP, SLOW_DOWN_DIST):
      self._perform_experimental_mode(AEM_COOLDOWN_STOP)

    # Green light resume - standstill, no lead, model path extends for N frames → clear AEM
    if self._active and v_ego < STANDSTILL_THRESHOLD and not radar_msg.leadOne.status and \
      len(model_msg.position.x) == ModelConstants.IDX_N and \
      model_msg.position.x[ModelConstants.IDX_N - 1] > GREEN_LIGHT_X_THRESHOLD:
      self._green_light_counter += 1
      if self._green_light_counter >= GREEN_LIGHT_FRAMES:
        self._cooldown_end_time = 0.0
    else:
      self._green_light_counter = 0

    # TTC-based triggering - lead car braking hard
    if v_ego > MIN_SPEED_FOR_TTC and radar_msg.leadOne.status:
      # vRel is negative when closing in on lead
      closing_speed = -radar_msg.leadOne.vRel
      if closing_speed > MIN_CLOSING_SPEED:
        d_rel = radar_msg.leadOne.dRel
        if d_rel > 0:
          ttc = d_rel / closing_speed
          if ttc < TTC_THRESHOLD:
            self._perform_experimental_mode(AEM_COOLDOWN_TTC)
