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
        "key": "dp_lat_offset_cm",
        "type": "spin_button_item",
        "title": lambda: tr("Position Offset"),
        "description": lambda: tr("Fine-tune where the car drives within the lane. Positive values move the car left, negative values move right.<br>Recommended to start with small values (±5cm) and adjust based on preference."),
        "default": 0,
        "min_val": -15,
        "max_val": 15,
        "step": 1,
        "suffix": lambda: tr("cm"),
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
