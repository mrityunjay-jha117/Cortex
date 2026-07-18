import os
import re

src_file = "cognitive_automator/gui/panels/property_panel.py"
dest_dir = "cognitive_automator/gui/panels/property_panel"

if os.path.exists(src_file):
    os.rename(src_file, "cognitive_automator/gui/panels/property_panel_old.py")

os.makedirs(dest_dir, exist_ok=True)

with open("cognitive_automator/gui/panels/property_panel_old.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the indices
build_marker_idx = 0
widget_helpers_idx = 0

for i, line in enumerate(lines):
    if "def _build_marker" in line:
        build_marker_idx = i
        break

for i, line in enumerate(lines):
    if "Widget helpers" in line:
        widget_helpers_idx = i - 2
        break

imports_and_init = lines[:build_marker_idx]
builders = lines[build_marker_idx:widget_helpers_idx]
helpers = lines[widget_helpers_idx:]

# We need to change the class definition in imports_and_init
# from `class PropertyPanel(QWidget):` to `class PropertyPanel(PropertyPanelBuilders, PropertyPanelHelpers, QWidget):`
new_imports = []
for line in imports_and_init:
    if line.startswith("class PropertyPanel(QWidget):"):
        new_imports.append("from .builders import PropertyPanelBuilders\n")
        new_imports.append("from .helpers import PropertyPanelHelpers\n")
        new_imports.append("class PropertyPanel(PropertyPanelBuilders, PropertyPanelHelpers, QWidget):\n")
    else:
        new_imports.append(line)

# For builders and helpers, we need to wrap them in their classes and include imports
common_imports = "".join(lines[:44]) # Everything up to ImageViewer class

builders_content = common_imports + "\nclass PropertyPanelBuilders:\n"
for line in builders:
    builders_content += line

helpers_content = common_imports + "\nclass PropertyPanelHelpers:\n"
for line in helpers:
    # skip the "Widget helpers" comment lines
    if line.startswith("    # -") or "Widget helpers" in line:
        continue
    helpers_content += line

base_content = "".join(new_imports)

files_to_write = {
    "__init__.py": "from .base import PropertyPanel, ImageViewer\n",
    "base.py": base_content,
    "builders.py": builders_content,
    "helpers.py": helpers_content,
}

for fname, fcontent in files_to_write.items():
    with open(os.path.join(dest_dir, fname), "w", encoding="utf-8") as f:
        f.write(fcontent)
