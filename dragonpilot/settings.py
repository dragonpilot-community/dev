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
    "settings": [

    ],
  },
  {
    "title": "Device",
    "settings": [
      {
        "key": "dp_dev_dashy",
        "type": "toggle_item",
        "title": lambda: tr("dashy HUD"),
        "description": lambda: tr("dashy - dragonpilot's all-in-one system hub for you.<br><br>Visit http://<device_ip>:5088 to access.<br><br>Enable this to use HUD feature (live streaming)."),
      },

    ],
  },
]
