#!/usr/bin/env python3
"""
Copyright (c) 2026, Rick Lan

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

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

GPS Location Service - Fuses GPS with livePose for smooth position output.

States:
  INITIALIZING: Waiting for first GPS fix
  CALIBRATING: Collecting yaw offset samples (need to be moving > 5 m/s)
  RUNNING: Outputting calibrated dead-reckoned position
  RECALIBRATING: Drift detected, blending back to GPS
"""
import json
import numpy as np
from enum import Enum

import cereal.messaging as messaging
from openpilot.common.params import Params
from openpilot.common.realtime import config_realtime_process
from openpilot.common.transformations.coordinates import geodetic2ecef, ecef2geodetic, LocalCoord
from openpilot.common.swaglog import cloudlog
from openpilot.common.gps import get_gps_location_service


class State(Enum):
  INITIALIZING = 0
  CALIBRATING = 1
  RUNNING = 2
  RECALIBRATING = 3


class LiveGPS:
  # Calibration
  CALIB_MIN_SPEED = 5.0       # m/s - need speed for reliable GPS bearing
  CALIB_MIN_SAMPLES = 5       # yaw samples needed
  CALIB_MAX_TIME = 30.0       # seconds before timeout

  # Recalibration triggers
  RECALIB_POS_ERROR = 30.0    # meters - triggers gradual recalib
  RECALIB_POS_HARD = 500.0    # meters - triggers hard reset
  RECALIB_YAW_ERROR = 0.785   # 45 degrees in radians
  RECALIB_YAW_HARD = 1.571    # 90 degrees in radians
  RECALIB_GPS_LOST = 10.0     # seconds

  # GPS quality
  GPS_MAX_ACCURACY = 30.0     # meters - reject worse
  GPS_MAX_JUMP = 50.0         # meters - reject jumps
  GPS_MAX_SPEED = 100.0       # m/s (~360 km/h)

  # Smoothing
  MAX_POS_CORRECTION = 10.0   # m/s max correction rate
  MAX_YAW_CORRECTION = 0.524  # 30 deg/s in radians
  STATIONARY_SPEED = 0.5      # m/s

  def __init__(self):
    self.state = State.INITIALIZING

    # GPS raw data
    self.last_gps_pos = None    # [lat, lon, alt]
    self.gps_speed = 0.0
    self.gps_bearing = 0.0
    self.gps_accuracy_h = 100.0
    self.gps_accuracy_v = 100.0
    self.gps_quality = 1.0      # 0-1 weight
    self.unix_timestamp_millis = 0

    # Position tracking (NED frame)
    self.local_coord = None
    self.pos_ned = np.zeros(3)
    self.pos_error = np.zeros(3)
    self.target_pos = np.zeros(3)

    # livePose data
    self.orientation_ned = np.zeros(3)
    self.vel_device = np.zeros(3)

    # Yaw calibration
    self.yaw_offset = 0.0
    self.yaw_offset_valid = False
    self.yaw_samples = []
    self.target_yaw = 0.0

    # Timing
    self.last_t = None
    self.last_gps_t = 0.0
    self.calib_start_t = 0.0

  def get_yaw(self):
    """Get calibrated absolute yaw."""
    if self.yaw_offset_valid:
      return (self.orientation_ned[2] + self.yaw_offset) % (2 * np.pi)
    return np.radians(self.gps_bearing)

  def _check_gps_valid(self, gps):
    """Check if GPS data is usable."""
    if abs(gps.latitude) < 0.1 or abs(gps.longitude) < 0.1:
      return False
    if abs(gps.latitude) > 90 or abs(gps.longitude) > 180:
      return False
    return gps.hasFix or gps.unixTimestampMillis > 0

  def _check_gps_quality(self, t, gps):
    """Check quality and detect jumps. Returns (accept, weight)."""
    # Unknown accuracy = assume decent
    accuracy = gps.horizontalAccuracy if gps.horizontalAccuracy > 0 else 8.0

    # Reject known bad accuracy
    if gps.horizontalAccuracy > self.GPS_MAX_ACCURACY:
      return False, 0.0

    # Jump detection
    if self.last_gps_pos is not None and self.last_gps_t > 0:
      dt = t - self.last_gps_t
      if dt > 0.01:
        last_ecef = geodetic2ecef(self.last_gps_pos)
        curr_ecef = geodetic2ecef([gps.latitude, gps.longitude, gps.altitude])
        distance = np.linalg.norm(np.array(curr_ecef) - np.array(last_ecef))
        if distance > max(self.GPS_MAX_JUMP, self.GPS_MAX_SPEED * dt):
          return False, 0.0

    # Weight by accuracy (5m = 1.0, 30m = 0.17)
    weight = min(1.0, 5.0 / max(accuracy, 1.0))
    return True, max(0.1, weight)

  def handle_gps(self, t, gps):
    """Process GPS update."""
    if not self._check_gps_valid(gps):
      return

    accept, weight = self._check_gps_quality(t, gps)

    # Always store for display (even if rejected)
    self.last_gps_pos = [gps.latitude, gps.longitude, gps.altitude]
    self.gps_speed = gps.speed
    self.gps_bearing = gps.bearingDeg

    if not accept:
      # Allow poor GPS for initialization only
      if self.state == State.INITIALIZING:
        weight = 0.1
      else:
        return

    # Store quality data
    self.gps_accuracy_h = gps.horizontalAccuracy if gps.horizontalAccuracy > 0 else 10.0
    self.gps_accuracy_v = gps.verticalAccuracy if gps.verticalAccuracy > 0 else 20.0
    self.gps_quality = weight
    self.last_gps_t = t
    self.unix_timestamp_millis = gps.unixTimestampMillis

    # State machine
    if self.state == State.INITIALIZING:
      self._init_position(gps)
      self.state = State.CALIBRATING
      self.calib_start_t = t
      self.yaw_samples = []
      cloudlog.info("LiveGPS: GPS acquired, calibrating")

    elif self.state == State.CALIBRATING:
      self._calibrate(t, gps)

    elif self.state == State.RUNNING:
      self._update_running(t, gps)

    elif self.state == State.RECALIBRATING:
      self._recalibrate(t, gps)

  def _init_position(self, gps):
    """Initialize local coordinate frame."""
    self.local_coord = LocalCoord.from_geodetic([gps.latitude, gps.longitude, gps.altitude])
    self.pos_ned = np.zeros(3)
    self.pos_error = np.zeros(3)

  def _collect_yaw_sample(self, gps):
    """Collect yaw calibration sample if conditions met."""
    if gps.speed > self.CALIB_MIN_SPEED and self.gps_quality > 0.3:
      gps_yaw = np.radians(gps.bearingDeg)
      pose_yaw = self.orientation_ned[2]
      offset = np.arctan2(np.sin(gps_yaw - pose_yaw), np.cos(gps_yaw - pose_yaw))
      self.yaw_samples.append(offset)

  def _calibrate(self, t, gps):
    """Calibration state: collect yaw samples."""
    self._collect_yaw_sample(gps)

    if len(self.yaw_samples) >= self.CALIB_MIN_SAMPLES:
      self.yaw_offset = float(np.median(self.yaw_samples))
      self.yaw_offset_valid = True
      self._init_position(gps)
      self.state = State.RUNNING
      cloudlog.info(f"LiveGPS: calibrated, yaw_offset={np.degrees(self.yaw_offset):.1f}deg")

    elif t - self.calib_start_t > self.CALIB_MAX_TIME:
      if self.yaw_samples:
        self.yaw_offset = float(np.median(self.yaw_samples))
        self.yaw_offset_valid = True
      self._init_position(gps)
      self.state = State.RUNNING
      cloudlog.warning("LiveGPS: calibration timeout")

  def _update_running(self, t, gps):
    """Running state: update position error and check for drift."""
    gps_ecef = geodetic2ecef([gps.latitude, gps.longitude, gps.altitude])
    gps_ned = self.local_coord.ecef2ned(gps_ecef)
    self.pos_error = gps_ned - self.pos_ned

    pos_error_mag = np.linalg.norm(self.pos_error[:2])
    gps_age = t - self.last_gps_t

    # Check for hard reset conditions
    if pos_error_mag > self.RECALIB_POS_HARD or gps_age > self.RECALIB_GPS_LOST * 3:
      cloudlog.warning(f"LiveGPS: hard reset, error={pos_error_mag:.1f}m")
      self._init_position(gps)
      self.yaw_offset_valid = False
      self.state = State.CALIBRATING
      self.calib_start_t = t
      self.yaw_samples = []
      return

    # Check yaw drift
    if gps.speed > self.CALIB_MIN_SPEED and self.gps_quality > 0.3:
      gps_yaw = np.radians(gps.bearingDeg)
      new_offset = np.arctan2(np.sin(gps_yaw - self.orientation_ned[2]),
                              np.cos(gps_yaw - self.orientation_ned[2]))
      diff = abs(np.arctan2(np.sin(new_offset - self.yaw_offset),
                            np.cos(new_offset - self.yaw_offset)))

      if diff > self.RECALIB_YAW_HARD:
        cloudlog.warning(f"LiveGPS: yaw reset, diff={np.degrees(diff):.1f}deg")
        self.yaw_offset = new_offset
        self._init_position(gps)
      elif diff > self.RECALIB_YAW_ERROR:
        cloudlog.warning(f"LiveGPS: yaw drift, diff={np.degrees(diff):.1f}deg")
        self.state = State.RECALIBRATING
        self.calib_start_t = t
        self.yaw_samples = []
        self.target_yaw = new_offset
        self.target_pos = gps_ned
      else:
        # Slow adaptation
        alpha = 0.1 * self.gps_quality
        self.yaw_offset += alpha * np.arctan2(np.sin(new_offset - self.yaw_offset),
                                               np.cos(new_offset - self.yaw_offset))

    # Check position drift
    if pos_error_mag > self.RECALIB_POS_ERROR:
      cloudlog.warning(f"LiveGPS: pos drift, error={pos_error_mag:.1f}m")
      self.state = State.RECALIBRATING
      self.calib_start_t = t
      self.yaw_samples = []
      self.target_pos = gps_ned

    # Reset anchor if drifted too far
    if np.linalg.norm(self.pos_ned[:2]) > 100:
      self._init_position(gps)

  def _recalibrate(self, t, gps):
    """Recalibrating state: blend back to GPS."""
    gps_ecef = geodetic2ecef([gps.latitude, gps.longitude, gps.altitude])
    self.target_pos = self.local_coord.ecef2ned(gps_ecef)

    self._collect_yaw_sample(gps)
    if len(self.yaw_samples) >= 3:
      self.target_yaw = float(np.median(self.yaw_samples[-10:]))

    # Check if done
    pos_error = np.linalg.norm(self.target_pos - self.pos_ned)
    if pos_error < 5.0 and len(self.yaw_samples) >= self.CALIB_MIN_SAMPLES:
      self.yaw_offset = self.target_yaw
      self.state = State.RUNNING
      cloudlog.info(f"LiveGPS: recalibrated, error={pos_error:.1f}m")
    elif t - self.calib_start_t > self.CALIB_MAX_TIME:
      if self.yaw_samples:
        self.yaw_offset = float(np.median(self.yaw_samples))
      self.state = State.RUNNING
      cloudlog.warning(f"LiveGPS: recalib timeout, error={pos_error:.1f}m")

  def handle_pose(self, t, pose):
    """Process livePose update - dead-reckon position."""
    if pose.orientationNED.valid:
      self.orientation_ned = np.array([pose.orientationNED.x, pose.orientationNED.y, pose.orientationNED.z])
    if pose.velocityDevice.valid:
      self.vel_device = np.array([pose.velocityDevice.x, pose.velocityDevice.y, pose.velocityDevice.z])

    if self.state not in (State.RUNNING, State.RECALIBRATING) or self.local_coord is None:
      self.last_t = t
      return

    if self.last_t is None:
      self.last_t = t
      return

    dt = t - self.last_t
    if dt <= 0 or dt > 1.0:
      self.last_t = t
      return

    # Stationary detection
    speed = np.linalg.norm(self.vel_device[:2])
    is_stationary = speed < self.STATIONARY_SPEED and self.gps_speed < self.STATIONARY_SPEED

    # Yaw blending during recalibration
    if self.state == State.RECALIBRATING and self.yaw_samples:
      yaw_diff = np.arctan2(np.sin(self.target_yaw - self.yaw_offset),
                            np.cos(self.target_yaw - self.yaw_offset))
      yaw_rate = 0.9 if abs(yaw_diff) > 0.5 else 0.5
      correction = np.clip(yaw_rate * dt * yaw_diff, -self.MAX_YAW_CORRECTION * dt, self.MAX_YAW_CORRECTION * dt)
      self.yaw_offset += correction

    # Transform velocity to NED
    yaw = self.get_yaw()
    cos_yaw, sin_yaw = np.cos(yaw), np.sin(yaw)
    vel_ned = np.array([
      cos_yaw * self.vel_device[0] - sin_yaw * self.vel_device[1],
      sin_yaw * self.vel_device[0] + cos_yaw * self.vel_device[1],
      self.vel_device[2]
    ])

    # Integrate position (skip if stationary)
    if not is_stationary:
      self.pos_ned += vel_ned * dt

    # Position correction
    if is_stationary:
      correction = self.pos_error * 0.05 * dt
    elif self.state == State.RECALIBRATING:
      error = self.target_pos - self.pos_ned
      rate = 0.95 if np.linalg.norm(error[:2]) > 50 else 0.4
      correction = error * rate * self.gps_quality * dt
    else:
      correction = self.pos_error * 0.8 * self.gps_quality * dt

    # Cap correction
    mag = np.linalg.norm(correction[:2])
    max_corr = self.MAX_POS_CORRECTION * dt
    if mag > max_corr:
      correction *= max_corr / mag

    self.pos_ned += correction
    if self.state == State.RUNNING:
      self.pos_error -= correction

    self.last_t = t

  def get_msg(self, log_mono_time):
    """Build liveGPS message."""
    msg = messaging.new_message('liveGPS')
    msg.logMonoTime = log_mono_time
    gps = msg.liveGPS

    t = log_mono_time * 1e-9
    gps_age = t - self.last_gps_t
    is_valid = self.state in (State.RUNNING, State.RECALIBRATING)
    gps_ok = is_valid and gps_age < 5.0

    if is_valid and self.local_coord is not None:
      pos_ecef = self.local_coord.ned2ecef(self.pos_ned)
      geodetic = ecef2geodetic(pos_ecef)
      gps.latitude = float(geodetic[0])
      gps.longitude = float(geodetic[1])
      gps.altitude = float(geodetic[2])
      gps.bearingDeg = float(np.degrees(self.get_yaw()) % 360)
      gps.speed = float(np.linalg.norm(self.vel_device[:2]))
      gps.horizontalAccuracy = float(self.gps_accuracy_h + np.linalg.norm(self.pos_ned[:2]) * 0.1)
      gps.verticalAccuracy = float(self.gps_accuracy_v)
      gps.status = 'valid' if gps_ok else ('recalibrating' if self.state == State.RECALIBRATING else 'gpsStale')

    elif self.last_gps_pos is not None:
      gps.latitude = float(self.last_gps_pos[0])
      gps.longitude = float(self.last_gps_pos[1])
      gps.altitude = float(self.last_gps_pos[2])
      gps.speed = float(self.gps_speed)
      gps.bearingDeg = float(self.gps_bearing)
      gps.horizontalAccuracy = float(self.gps_accuracy_h) if self.gps_accuracy_h > 0 else 50.0
      gps.verticalAccuracy = float(self.gps_accuracy_v) if self.gps_accuracy_v > 0 else 50.0
      gps.status = 'calibrating' if self.state == State.CALIBRATING else 'initializing'

    else:
      gps.latitude = 0.0
      gps.longitude = 0.0
      gps.altitude = 0.0
      gps.speed = 0.0
      gps.bearingDeg = 0.0
      gps.horizontalAccuracy = 100.0
      gps.verticalAccuracy = 100.0
      gps.status = 'noGps'

    gps.gpsOK = gps_ok
    gps.unixTimestampMillis = self.unix_timestamp_millis
    gps.lastGpsTimestamp = int(self.last_gps_t * 1e9) if self.last_gps_t > 0 else 0

    return msg


def main():
  config_realtime_process([0, 1, 2, 3], 5)

  params = Params()
  gps_service = get_gps_location_service(params)
  cloudlog.info(f"LiveGPS: using {gps_service}")

  pm = messaging.PubMaster(['liveGPS'])
  sm = messaging.SubMaster([gps_service, 'livePose'], poll='livePose', ignore_alive=[gps_service])

  gps = LiveGPS()

  # Load last GPS position or default to Taipei 101
  try:
    last_pos = params.get("LastGPSPosition")
    if last_pos:
      pos_data = json.loads(last_pos)
      gps.last_gps_pos = [pos_data['latitude'], pos_data['longitude'], pos_data['altitude']]
      cloudlog.info(f"LiveGPS: loaded last position: {gps.last_gps_pos}")
    else:
      raise ValueError("No saved position")
  except Exception:
    gps.last_gps_pos = [25.033976, 121.564472, 10.0]  # Taipei 101
    cloudlog.info("LiveGPS: using default position (Taipei 101)")

  while True:
    sm.update()

    if sm.updated[gps_service] and sm.valid[gps_service]:
      gps.handle_gps(sm.logMonoTime[gps_service] * 1e-9, sm[gps_service])

    if sm.updated['livePose']:
      if sm.valid['livePose']:
        gps.handle_pose(sm.logMonoTime['livePose'] * 1e-9, sm['livePose'])

      msg = gps.get_msg(sm.logMonoTime['livePose'])
      pm.send('liveGPS', msg)

      # Save position periodically
      if sm.frame % 1200 == 0 and gps.state == State.RUNNING and gps.last_gps_pos:
        if (sm.logMonoTime['livePose'] * 1e-9 - gps.last_gps_t) < 5.0:
          params.put("LastGPSPosition", json.dumps({
            'latitude': gps.last_gps_pos[0],
            'longitude': gps.last_gps_pos[1],
            'altitude': gps.last_gps_pos[2]
          }))


if __name__ == "__main__":
  main()
