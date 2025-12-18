try:
  from dragonpilot.system.ui.lib.multilang import tr
except:
  from openpilot.system.ui.lib.multilang import tr

SETTINGS = [
  {
    "title": "Toyota / Lexus",
    "condition": "brand == 'toyota'",
    "settings": [

    ],
  },
  {
    "title": "VAG",
    "condition": "brand == 'volkswagen'",
    "settings": [

    ],
  },
  {
    "title": "Mazda",
    "condition": "brand == 'mazda'",
    "settings": [

    ],
  },
  {
    "title": "Lateral",
    "settings": [
      {
        "key": "dp_lat_lca_speed",
        "type": "spin_button_item",
        "title": lambda: tr("Lane Change Assist At:"),
        "description": lambda: tr("Off = Disable LCA.<br>1 mph = 1.2 km/h."),
        "default": 20,
        "min_val": 0,
        "max_val": 100,
        "step": 5,
        "suffix": lambda: tr("mph"),
        "special_value_text": lambda: tr("Off"),
        "on_change": [{
          "target": "dp_lat_lca_auto_sec",
          "action": "set_enabled",
          "condition": "value > 0"
        }]
      },
      {
        "key": "dp_lat_lca_auto_sec",
        "type": "double_spin_button_item",
        "title": lambda: tr("+ Auto Lane Change after:"),
        "description": lambda: tr("Off = Disable Auto Lane Change."),
        "default": 0.0,
        "min_val": 0.0,
        "max_val": 5.0,
        "step": 0.5,
        "suffix": lambda: tr("sec"),
        "special_value_text": lambda: tr("Off"),
        "initially_enabled_by": {
          "param": "dp_lat_lca_speed",
          "condition": "value > 0",
          "default": 20
        }
      },

    ],
  },
  {
    "title": "Longitudinal",
    "condition": "openpilotLongitudinalControl",
    "settings": [

    ],
  },
  {
    "title": "UI",
    "condition": "not MICI",
    "settings": [

    ],
  },
  {
    "title": "Device",
    "settings": [

    ],
  },
]
