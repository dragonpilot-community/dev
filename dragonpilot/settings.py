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
      {
        "key": "dp_lon_aem",
        "type": "toggle_item",
        "title": "Adaptive Experimental Mode (AEM)",
        "description": "Adaptive mode switcher between ACC and Blended based on driving context."
      },

    ],
  },
  {
    "title": "UI",
    "settings": [

    ],
  },
  {
    "title": "Device",
    "settings": [

    ],
  },
]
