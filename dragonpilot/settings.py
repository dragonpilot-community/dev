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
        "key": "dp_lat_road_edge_detection",
        "type": "toggle_item",
        "title": lambda: tr("Road Edge Detection (RED)"),
        "description": lambda: tr("Block lane change assist when the system detects the road edge.<br>NOTE: This will show 'Car Detected in Blindspot' warning."),
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
