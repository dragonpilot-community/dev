import os
from openpilot.system.ui.widgets import Widget, DialogResult
from openpilot.common.params import Params, UnknownKeyName
from openpilot.selfdrive.ui.ui_state import ui_state
from openpilot.system.ui.widgets.scroller import Scroller
from openpilot.system.ui.lib.multilang import tr, tr_noop
from openpilot.system.ui.widgets.list_view import multiple_button_item, toggle_item, simple_item, button_item, spin_button_item, double_spin_button_item, text_spin_button_item
from openpilot.system.ui.lib.application import gui_app
from openpilot.system.ui.widgets.confirm_dialog import ConfirmDialog, alert_dialog

DESC_TOYOTA = {

}

DESC_VAG = {

}

DESC_MAZDA = {

}

DESC_LAT = {

}

DESC_LON = {

}

DESC_UI = {

}

DESC_DEV = {

}

DESC = {
  "dp_dev_reset_conf": tr_noop("Reset dragonpilot settings to default and restart the device."),
}

class DragonpilotLayout(Widget):
  def __init__(self):
    super().__init__()
    self._params = Params()
    self._scroller: Scroller | None = None
    self._list = []
    self._has_long_ctrl = False
    self._has_radar_unavailable = False

    self._toggles = {}
    self._locked_toggles = set()

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

    self._reset_dp_conf_btn = button_item(lambda: tr("Reset DP Settings"), lambda: tr("RESET"), lambda: tr(DESC['dp_dev_reset_conf']), callback=self._reset_dp_conf)
    self._toggles['btn_reset_dp_conf'] = self._reset_dp_conf_btn

    self._scroller = Scroller(list(self._toggles.values()), line_separator=True, spacing=0)

  def _add_toggle(self, param, title, desc, icon, needs_restart):
      toggle = toggle_item(
        title,
        desc,
        self._params.get_bool(param),
        callback=lambda state, p=param: self._toggle_callback(state, p),
        icon=icon,
      )

      try:
        locked = self._params.get_bool(param + "Lock")
      except UnknownKeyName:
        locked = False
      toggle.action_item.set_enabled(not locked)

      # Make description callable for live translation
      additional_desc = ""
      if needs_restart and not locked:
        additional_desc = tr("Changing this setting will restart openpilot if the car is powered on.")
      toggle.set_description(lambda og_desc=toggle.description, add_desc=additional_desc: tr(og_desc) + (" " + tr(add_desc) if add_desc else ""))

      # track for engaged state updates
      if locked:
        self._locked_toggles.add(param)

      self._toggles[param] = toggle

  def _toyota_toggles(self):
    self._toggles["title_toyota"] = simple_item(tr("### Toyota / Lexus ###"))
    # create the toggle list
    _toggle_defs = {

    }

    # process toggles
    for param, (title, desc, icon, needs_restart) in _toggle_defs.items():
      self._add_toggle(param=param, title=title, desc=desc, icon=icon, needs_restart=needs_restart)

  def _vag_toggles(self):
    self._toggles["title_vag"] = simple_item(tr("### VAG ###"))
    # create the toggle list
    _toggle_defs = {

    }

    # process toggles
    for param, (title, desc, icon, needs_restart) in _toggle_defs.items():
      self._add_toggle(param=param, title=title, desc=desc, icon=icon, needs_restart=needs_restart)
    pass

  def _mazda_toggles(self):
    self._toggles["title_mazda"] = simple_item(tr("### Mazda ###"))
    # create the toggle list
    _toggle_defs = {

    }

    # process toggles
    for param, (title, desc, icon, needs_restart) in _toggle_defs.items():
      self._add_toggle(param=param, title=title, desc=desc, icon=icon, needs_restart=needs_restart)
    pass

  def _lat_toggles(self):
    self._toggles["title_lat"] = simple_item(tr("### Lateral ###"))
    # create the toggle list
    _toggle_defs = {

    }

    # process toggles
    for param, (title, desc, icon, needs_restart) in _toggle_defs.items():
      self._add_toggle(param=param, title=title, desc=desc, icon=icon, needs_restart=needs_restart)
    pass

  def _lon_toggles(self):
    self._toggles["title_lon"] = simple_item(tr("### Longitudinal ###"))
    # create the toggle list
    _toggle_defs = {

    }

    # process toggles
    for param, (title, desc, icon, needs_restart) in _toggle_defs.items():
      self._add_toggle(param=param, title=title, desc=desc, icon=icon, needs_restart=needs_restart)
    pass

  def _ui_toggles(self):
    self._toggles["title_ui"] = simple_item(tr("### UI ###"))
    # create the toggle list
    _toggle_defs = {

    }

    # process toggles
    for param, (title, desc, icon, needs_restart) in _toggle_defs.items():
      self._add_toggle(param=param, title=title, desc=desc, icon=icon, needs_restart=needs_restart)
    pass

  def _device_toggles(self):
    self._toggles["title_dev"] = simple_item(tr("### Device ###"))
    # create the toggle list
    _toggle_defs = {

    }

    # process toggles
    for param, (title, desc, icon, needs_restart) in _toggle_defs.items():
      self._add_toggle(param=param, title=title, desc=desc, icon=icon, needs_restart=needs_restart)
    pass


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

  def _toggle_callback(self, state: bool, param: str):
    pass
