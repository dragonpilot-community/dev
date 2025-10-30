import os
from openpilot.system.ui.widgets import Widget, DialogResult
from openpilot.common.params import Params, UnknownKeyName
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.widgets.scroller import Scroller
from openpilot.system.ui.lib.multilang import tr, tr_noop
from openpilot.system.ui.widgets.list_view import multiple_button_item, toggle_item, simple_item, button_item, spin_button_item, double_spin_button_item, text_spin_button_item
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog, alert_dialog


class DragonpilotLayout(Widget):
  def __init__(self):
    super().__init__()
    self._params = Params()
    self._scroller: Scroller | None = None
    self._has_long_ctrl = False
    self._has_radar_unavailable = False

    self._toggles = {}

    if ui_state.CP is not None:
      self._has_long_ctrl = ui_state.CP.openpilotLongitudinalControl
      self._has_radar_unavailable = ui_state.CP.radarUnavailable
      match ui_state.CP.brand:
        case "toyota":
          self._toyota_toggles()
        case "volkswagen":
          self._vag_toggles()
        case "mazda":
          self._mazda_toggles()

    self._lat_toggles()
    self._lon_toggles()
    self._ui_toggles()
    self._device_toggles()

    self._reset_dp_conf_btn = button_item(
      lambda: tr("Reset DP Settings"),
      lambda: tr("RESET"),
      lambda: tr("Reset dragonpilot settings to default and restart the device."),
      callback=self._reset_dp_conf)

    self._toggles['btn_reset_dp_conf'] = self._reset_dp_conf_btn

    self._scroller = Scroller(list(self._toggles.values()), line_separator=True, spacing=0)

  def _toyota_toggles(self):
    self._toggles["title_toyota"] = simple_item(title=lambda: tr("### Toyota / Lexus ###"))

  def _vag_toggles(self):
    self._toggles["title_vag"] = simple_item(title=lambda: tr("### VAG ###"))

  def _mazda_toggles(self):
    self._toggles["title_mazda"] = simple_item(title=lambda: tr("### Mazda ###"))

  def _lat_toggles(self):
    self._toggles["title_lat"] = simple_item(title=lambda: tr("### Lateral ###"))

  def _lon_toggles(self):
    self._toggles["title_lon"] = simple_item(title=lambda: tr("### Longitudinal ###"))

  def _ui_toggles(self):
    self._toggles["title_ui"] = simple_item(title=lambda: tr("### UI ###"))

  def _device_toggles(self):
    self._toggles["title_dev"] = simple_item(title=lambda: tr("### Device ###"))

  def _reset_dp_conf(self):
    def reset_dp_conf(result: int):
      # Check engaged again in case it changed while the dialog was open
      if result != DialogResult.CONFIRM:
        return
      self._params.put_bool_nonblocking("dp_dev_reset_conf", True)

    dialog = ConfirmDialog(tr("Are you sure you want to reset ALL DP SETTINGS to default?"), tr("Reset"))
    gui_app.set_modal_overlay(dialog, callback=reset_dp_conf)

  def show_event(self):
    self._scroller.show_event()
    self._update_toggles()

  def _update_toggles(self):
    ui_state.update_params()

  def _render(self, rect):
    self._scroller.render(rect)
