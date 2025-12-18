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
        "key": "dp_ui_display_mode",
        "type": "text_spin_button_item",
        "title": lambda: tr("Display Mode"),
        "description": lambda: tr("Std.: Stock behavior.<br>MAIN+: ACC MAIN on = Display ON.<br>OP+: OP enabled = Display ON.<br>MAIN-: ACC MAIN on = Display OFF<br>OP-: OP enabled = Display OFF."),
        "default": 0,
        "options": [
          lambda: tr("Std."),
          lambda: tr("MAIN+"),
          lambda: tr("OP+"),
          lambda: tr("MAIN-"),
          lambda: tr("OP-"),
        ],
      },

    ],
  },
  {
    "title": "Device",
    "settings": [

    ],
  },
]
