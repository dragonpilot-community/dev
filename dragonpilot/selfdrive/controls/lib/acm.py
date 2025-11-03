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

import numpy as np

CRUISE_RATIO = 0.98
TTC_LIMIT = 3.5
MIN_V_EGO = 8.5 # approx. 30 km/h
SAFE_DIST_MIN = 20.0
SAFE_DIST_COEFF = 1.2  # time gap multiplier
MIN_BRAKE_ALLOW = -0.5


class ACM:
  def __init__(self):
    self.enabled = False
    self.active = False
    self._is_speed_over_cruise = False
    self._has_lead = False
    self.accel_coast = 0.
    self.debug = {}

  def update_states(self, cc, rs, user_ctrl_lon, v_ego, v_cruise, accel_coast):
    self.active = False
    self.accel_coast = accel_coast
    self._is_speed_over_cruise = v_ego > (v_cruise * CRUISE_RATIO)

    # no orientation (e.g. pitch)
    if not self.enabled or len(cc.orientationNED) != 3:
      return

    lead = rs.leadOne
    too_close = False
    too_fast_close = False

    if lead and lead.status:
      # --- TTC Calc ---
      v_rel = v_ego - lead.vLeadK if hasattr(lead, "vLeadK") else v_ego - (v_ego + lead.vRel)
      lead_ttc = lead.dRel / max(v_rel, 0.1)
      safe_dist = max(SAFE_DIST_MIN, v_ego * SAFE_DIST_COEFF)

      too_close = lead.dRel < safe_dist
      too_fast_close = lead_ttc < TTC_LIMIT or lead.vRel < -2.0

      self.debug.update({
        "dRel": lead.dRel,
        "vRel": lead.vRel,
        "lead_ttc": lead_ttc,
        "safe_dist": safe_dist,
        "too_close": too_close,
        "too_fast_close": too_fast_close,
      })
    else:
      self.debug.update({"lead": "none"})

    # === core logic ===
    self.active = (
      self.enabled and
      not user_ctrl_lon and
      self._is_speed_over_cruise and
      v_ego > MIN_V_EGO and
      not too_close and
      not too_fast_close
    )

  def update_a_desired_trajectory(self, a_desired_trajectory):
    if not self.active:
      return a_desired_trajectory
    # smooth
    return np.maximum(a_desired_trajectory, self.accel_coast)

  def update_output_a_target(self, output_a_target):
    if not self.active:
      return output_a_target
    # coast only
    return max(output_a_target, self.accel_coast)
