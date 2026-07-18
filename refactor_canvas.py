import os

src_file = "cognitive_automator/gui/canvas.py"
dest_dir = "cognitive_automator/gui/canvas"

if os.path.exists(src_file):
    os.rename(src_file, "cognitive_automator/gui/canvas_old.py")

os.makedirs(dest_dir, exist_ok=True)

with open("cognitive_automator/gui/canvas_old.py", "r", encoding="utf-8") as f:
    content = f.read()

parts = content.split("# ---------------------------------------------------------------------------")

imports = parts[0].strip() + "\n\n"
helpers = parts[12].strip() + "\n\n"

base_content = imports + helpers

# Add specific imports to fix circular references or unresolved types
port_content = "from .base import *\n" + parts[2].strip() + "\n"
node_content = "from .base import *\nfrom .port import PortItem\nfrom .edge import EdgeItem\n" + parts[4].strip() + "\n"
edge_content = "from .base import *\nfrom .port import PortItem\n" + parts[6].strip() + "\n"
scene_content = "from .base import *\nfrom .port import PortItem\nfrom .node import NodeItem\nfrom .edge import EdgeItem\n" + parts[8].strip() + "\n"
view_content = "from .base import *\nfrom .scene import GraphScene\n" + parts[10].strip() + "\n"

# But node_content needs GraphScene inside mouseDoubleClickEvent. We can import it locally or rely on dynamic typing.
# The code does: `cast_scene: GraphScene = self.scene()`
# If GraphScene is not imported at the top, it will cause a NameError at runtime.
# So we add `from .scene import GraphScene` to node_content, BUT that creates a circular import since scene imports node.
# However, Python allows circular imports if they are imported at the bottom or inside the method!
# Let's patch node_content to import GraphScene inside the method.
node_content = node_content.replace(
    "cast_scene: GraphScene = self.scene()",
    "from .scene import GraphScene\n            cast_scene: GraphScene = self.scene()"
)

files_to_write = {
    "base.py": base_content,
    "port.py": port_content,
    "node.py": node_content,
    "edge.py": edge_content,
    "scene.py": scene_content,
    "view.py": view_content,
}

init_content = "from .base import *\n"
init_content += "from .port import *\n"
init_content += "from .node import *\n"
init_content += "from .edge import *\n"
init_content += "from .scene import *\n"
init_content += "from .view import *\n"

files_to_write["__init__.py"] = init_content

for fname, fcontent in files_to_write.items():
    with open(os.path.join(dest_dir, fname), "w", encoding="utf-8") as f:
        f.write(fcontent)
