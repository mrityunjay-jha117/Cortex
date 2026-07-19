from ..base import *

def execute_write_file(node: WriteFileNode, context: dict[str, Any]) -> NodeResult:
    """Writes rendered content to a file."""
    try:
        content = render_prompt(node.content_template, context)
        mode = "a" if node.append else "w"
        
        # If content is a dict/list, format as JSON for convenience
        if isinstance(content, (dict, list)):
            import json
            content = json.dumps(content, indent=2)
            
        with open(node.file_path, mode, encoding="utf-8") as f:
            f.write(content)
            if node.append and not content.endswith("\n"):
                f.write("\n")
                
        log.info("WriteFile: saved to %s", node.file_path)
        return NodeResult(success=True, output_key=node.output_key, output_value="success")
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
