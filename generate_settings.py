#!/usr/bin/env python3
"""
Dragonpilot Settings Generator

Scans dragonpilot/settings/*.yaml, merges all entries, and generates:
- dragonpilot/settings.py (fresh)
- common/params_keys.h (with openpilot base preserved via markers)
"""

import yaml
from pathlib import Path
from typing import Dict, List

SCRIPT_DIR = Path(__file__).parent
SETTINGS_DIR = SCRIPT_DIR / "dragonpilot" / "settings"
SETTINGS_PY_OUT = SCRIPT_DIR / "dragonpilot" / "settings.py"
PARAMS_KEYS_H_OUT = SCRIPT_DIR / "common" / "params_keys.h"

SECTION_ORDER = [
    "Toyota / Lexus",
    "HKG",
    "VAG",
    "Mazda",
    "Lateral",
    "Longitudinal",
    "UI",
    "Device",
]


def find_yaml_files() -> List[Path]:
    """Find all YAML files in dragonpilot/settings/."""
    return sorted(SETTINGS_DIR.glob("*.yaml"))


def merge_yaml_files() -> Dict:
    """Load and merge all YAML files by section."""
    yaml_files = find_yaml_files()
    print(f"Found {len(yaml_files)} YAML files")

    sections_map = {}
    params_map = {}

    for f in yaml_files:
        print(f"  Merging {f.name}...")
        with open(f, "r") as fh:
            data = yaml.safe_load(fh)

            settings_list = data.get("settings", [])
            if isinstance(settings_list, list) and len(settings_list) > 0:
                first_item = settings_list[0]
                if "items" in first_item:
                    for section in settings_list:
                        title = section.get("title", "")
                        if title not in sections_map:
                            sections_map[title] = {
                                "title": title,
                                "condition": section.get("condition"),
                                "items": []
                            }
                        for item in section.get("items", []):
                            if "title" in item:
                                sections_map[title]["items"].append(item)
                            if "key" in item:
                                params_map[item["key"]] = {
                                    "key": item["key"],
                                    "flags": item.get("flags", "PERSISTENT"),
                                    "type": item.get("param_type", "BOOL"),
                                    "default": item.get("default", "0")
                                }
                elif "key" in first_item:
                    for item in settings_list:
                        category = item.get("category", "")
                        if category not in sections_map:
                            sections_map[category] = {
                                "title": category,
                                "condition": item.get("condition"),
                                "items": []
                            }
                        if "title" in item:
                            sections_map[category]["items"].append(item)
                        if "key" in item:
                            params_map[item["key"]] = {
                                "key": item["key"],
                                "flags": item.get("flags", "PERSISTENT"),
                                "type": item.get("param_type", "BOOL"),
                                "default": item.get("default", "0")
                            }

            for param in data.get("params_keys", []):
                params_map[param["key"]] = param

    # Sort sections by SECTION_ORDER
    sorted_sections = []
    for title in SECTION_ORDER:
        if title in sections_map:
            sorted_sections.append(sections_map[title])

    # Add any sections not in SECTION_ORDER at the end
    for title, section in sections_map.items():
        if title not in SECTION_ORDER:
            sorted_sections.append(section)

    return {
        "settings": sorted_sections,
        "params_keys": list(params_map.values())
    }


def generate_settings_py(data: Dict) -> str:
    """Generate settings.py (fresh)."""
    lines = [
        "try:",
        "  from dragonpilot.system.ui.lib.multilang import tr",
        "except:",
        "  from openpilot.system.ui.lib.multilang import tr",
        "",
        "SETTINGS = [",
    ]

    def esc(s):
        return s.replace("\\", "\\\\").replace('"', '\\"')

    def emit_item(item, indent=6):
        if "title" not in item:
            return
        prefix = " " * indent
        lines.append(prefix + "{")
        lines.append(f'{prefix}  "key": "{item["key"]}",')
        lines.append(f'{prefix}  "type": "{item.get("type", "toggle_item")}",')
        lines.append(f'{prefix}  "title": lambda: tr("{esc(item.get("title", item["key"]))}"),')

        if "description" in item:
            lines.append(f'{prefix}  "description": lambda: tr("{esc(item["description"])}"),')

        if "options" in item:
            opts = ", ".join(f'tr("{esc(o)}")' for o in item["options"])
            lines.append(f'{prefix}  "options": [{opts}],')

        if "default" in item:
            lines.append(f'{prefix}  "default": {item["default"]},')

        if "min_val" in item:
            lines.append(f'{prefix}  "min_val": {item["min_val"]},')
        if "max_val" in item:
            lines.append(f'{prefix}  "max_val": {item["max_val"]},')
        if "step" in item:
            lines.append(f'{prefix}  "step": {item["step"]},')

        if "suffix" in item:
            lines.append(f'{prefix}  "suffix": lambda: tr("{esc(item["suffix"])}"),')

        if "special_value_text" in item:
            lines.append(f'{prefix}  "special_value_text": lambda: tr("{esc(item["special_value_text"])}"),')

        if "brands" in item:
            brands = ", ".join(f'"{b}"' for b in item["brands"])
            lines.append(f'{prefix}  "brands": [{brands}],')

        if "condition" in item:
            lines.append(f'{prefix}  "condition": "{item["condition"]}",')

        if "on_change" in item:
            lines.append(f"{prefix}  \"on_change\": [")
            for oc in item["on_change"]:
                lines.append(f'{prefix}    {{"target": "{oc["target"]}", "action": "{oc["action"]}", "condition": "{oc["condition"]}"}},')
            lines.append(f"{prefix}  ],")

        if "initially_enabled_by" in item:
            ieb = item["initially_enabled_by"]
            lines.append(f'{prefix}  "initially_enabled_by": {{"param": "{ieb["param"]}", "condition": "{ieb["condition"]}", "default": {ieb["default"]}}}')

        lines.append(f"{prefix}}},")

    def emit_section(section, indent=2):
        prefix = " " * indent
        lines.append(prefix + "{")
        lines.append(f'{prefix}  "title": "{esc(section["title"])}",')
        if section.get("condition"):
            lines.append(f'{prefix}  "condition": "{section["condition"]}",')
        lines.append(f'{prefix}  "settings": [')
        for item in section.get("items", []):
            emit_item(item, indent + 4)
        lines.append(f"{prefix}  ],")
        lines.append(f"{prefix}}},")

    for section in data.get("settings", []):
        emit_section(section)

    lines.append("]")
    return "\n".join(lines)


def generate_params_keys_h(data: Dict) -> str:
    """Generate dragonpilot params section only."""
    lines = []

    for param in data.get("params_keys", []):
        key = param["key"]
        flags = param.get("flags", "PERSISTENT")
        ptype = param.get("type", "BOOL")
        default = param.get("default", "0")
        default_str = str(default)
        lines.append(f'    {{"{key}", {{{flags}, {ptype}, "{default_str}"}}}},')

    return lines


def update_params_keys_h(generated_dp_params: List[str]):
    """Append dragonpilot params to params_keys.h, skipping existing ones."""
    with open(PARAMS_KEYS_H_OUT, "r") as f:
        content = f.read()

    existing_keys = set()
    for line in content.split('\n'):
        import re
        m = re.search(r'\{\"dp_[^"]+\"', line)
        if m:
            existing_keys.add(m.group(0)[2:-1])

    new_lines = []
    for line in generated_dp_params:
        if line.strip():
            key_match = re.search(r'\{\"dp_[^\"]+\"', line)
            if key_match:
                key = key_match.group(0)[2:-1]
                if key not in existing_keys:
                    new_lines.append(line)

    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip() == '};':
            if new_lines:
                lines.insert(i, '\n'.join(new_lines))
            break

    with open(PARAMS_KEYS_H_OUT, "w") as f:
        f.write('\n'.join(lines))


def main():
    data = merge_yaml_files()

    # Generate settings.py (fresh)
    print(f"Generating {SETTINGS_PY_OUT}...")
    settings_content = generate_settings_py(data)
    with open(SETTINGS_PY_OUT, "w") as f:
        f.write(settings_content)
    print(f"  Written {len(settings_content.splitlines())} lines")

    # Generate and update params_keys.h (with markers)
    print(f"Generating dragonpilot params for {PARAMS_KEYS_H_OUT}...")
    dp_params = generate_params_keys_h(data)
    update_params_keys_h(dp_params)
    print("  Updated params_keys.h")


if __name__ == "__main__":
    main()
