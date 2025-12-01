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
      {
        "key": "dp_ui_lead",
        "type": "text_spin_button_item",
        "title": "Display Lead Stats",
        "description": "Display the statistics of lead car and/or radar tracking points.<br>Lead: Lead stats only<br>Radar: Radar tracking point stats only<br>All: Lead and Radar stats<br>NOTE: Radar option only works on certain vehicle models.",
        "default": 0,
        "options": [
          "Off",
          "Lead",
          "Radar",
          "All"
        ],
        "condition": "not MICI",
      },

    ],
  },
  {
    "title": "Device",
    "settings": [

    ],
  },
]
