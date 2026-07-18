import os
import shutil

src_file = "cognitive_automator/nodes/executors.py"
dest_dir = "cognitive_automator/nodes/executors"

if os.path.exists(src_file):
    os.rename(src_file, "cognitive_automator/nodes/executors_old.py")

os.makedirs(dest_dir, exist_ok=True)

with open("cognitive_automator/nodes/executors_old.py", "r", encoding="utf-8") as f:
    content = f.read()

# Split by the large dash separator
parts = content.split("# ---------------------------------------------------------------------------")

# parts[0] is the top imports and NodeResult definition
# parts[1] is "\n# Physical IO Executors\n"
# parts[2] is "\n\ndef execute_mouse..."
# Notice that split separates the dashed lines.
# The structure is:
# 0: Imports
# 1: \n# Physical IO Executors\n
# 2: \n\ndef execute_mouse...
# 3: \n# Vision Executors\n
# 4: \n\ndef execute_locate_element...
# 5: \n# LLM Executors\n
# 6: \n\ndef execute_judgment...
# 7: \n# Flow Executors\n
# 8: \n\ndef execute_wait...

imports = parts[0].strip() + "\n\n"

# But wait, `NodeResult` is in the imports. 
# We should probably put `NodeResult` in a `base.py` to avoid circular imports? 
# Actually, no, if we just copy the imports and NodeResult into every file, it's totally fine for this refactor!
# Python allows duplicate dataclass definitions across modules as long as they aren't strictly type-checked against each other (or they are, but here we can just put NodeResult in a `base.py` to be clean).
# Let's be clean.

base_content = imports

files_to_write = {
    "base.py": base_content,
    "physical.py": "from .base import *\n" + parts[2].strip() + "\n",
    "vision.py": "from .base import *\n" + parts[4].strip() + "\n",
    "llm.py": "from .base import *\n" + parts[6].strip() + "\n",
    "flow.py": "from .base import *\n" + parts[8].strip() + "\n",
}

# The __init__.py will export everything
init_content = "from .base import *\n"
init_content += "from .physical import *\n"
init_content += "from .vision import *\n"
init_content += "from .llm import *\n"
init_content += "from .flow import *\n"
files_to_write["__init__.py"] = init_content

for fname, fcontent in files_to_write.items():
    with open(os.path.join(dest_dir, fname), "w", encoding="utf-8") as f:
        f.write(fcontent)
