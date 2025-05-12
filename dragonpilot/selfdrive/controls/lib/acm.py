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


CRUISE_RATIO = 0.98

MIN_TTC = 3. # min TTC
MIN_V_EGO = 8. # minimum speed
MIN_DREL = 25.


class ACM:
  def __init__(self):
    self.enabled = False
    self._is_speed_over_cruise = False
    self.active = False

  def update_states(self, cs, rs, user_ctrl_lon, v_ego, v_cruise):
    if not self.enabled:
      self.active = False
      return

    self._is_speed_over_cruise = v_ego >= (v_cruise * CRUISE_RATIO)

    lead = rs.leadOne
    lead_ttc = lead.dRel / v_ego if lead.status and v_ego > 0 else float('inf')

    self.active = not user_ctrl_lon and \
                  self._is_speed_over_cruise and \
                  v_ego > MIN_V_EGO and \
                  (not lead.status or (lead.status and lead_ttc > MIN_TTC and lead.dRel > MIN_DREL))
