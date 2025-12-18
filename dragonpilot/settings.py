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
        "key": "dp_dev_auto_shutdown_in",
        "type": "spin_button_item",
        "title": lambda: tr("Auto Shutdown After"),
        "description": lambda: tr("0 min = Immediately"),
        "default": -5,
        "min_val": -5,
        "max_val": 300,
        "step": 5,
        "suffix": lambda: tr("min"),
        "special_value_text": lambda: tr("Off"),
      },

    ],
  },
]
