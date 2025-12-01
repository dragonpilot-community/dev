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
      {
        "key": "dp_dev_audible_alert_mode",
        "type": "text_spin_button_item",
        "title": "Audible Alert",
        "description": "Std.: Stock behaviour.<br>Warning: Only emits sound when there is a warning.<br>Off: Does not emit any sound at all.",
        "default": 0,
        "options": [
          "Std.",
          "Warning",
          "Off"
        ],
        "condition": "not LITE"
      },

    ],
  },
]
