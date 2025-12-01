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
        "key": "dp_dev_delay_loggerd",
        "type": "spin_button_item",
        "title": "Delay Starting Loggerd for:",
        "description": "Delays the startup of loggerd and its related processes when the device goes on-road.<br>This prevents the initial moments of a drive from being recorded, protecting location privacy at the start of a trip.",
        "default": 0,
        "min_val": 0,
        "max_val": 300,
        "step": 5,
        "suffix": " secs",
        "special_value_text": "Off"
      },

    ],
  },
]
