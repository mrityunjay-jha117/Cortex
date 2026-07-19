from ..base import *

def execute_csv_writer(node: CSVWriterNode, context: dict[str, Any]) -> NodeResult:
    """Writes data (dict or list[dict]) to a CSV file."""
    try:
        import os
        data = context.get(node.data_source_key)
        if data is None:
            return NodeResult(success=False, error=f"Data source key '{node.data_source_key}' not found in context")
            
        # Standardize to list of dicts
        if isinstance(data, dict):
            data = [data]
        elif not isinstance(data, list):
            return NodeResult(success=False, error=f"Data at '{node.data_source_key}' must be a dict or list of dicts")
            
        if not data:
            log.warning("CSVWriter: No data to write")
            return NodeResult(success=True)
            
        file_exists = os.path.isfile(node.file_path)
        mode = "a" if node.append else "w"
        
        # Extract headers from first row
        headers = list(data[0].keys())
        
        with open(node.file_path, mode, newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            # Write header if new file or overwriting
            if not file_exists or not node.append:
                writer.writeheader()
            writer.writerows(data)
            
        log.info("CSVWriter: wrote %d rows to %s", len(data), node.file_path)
        return NodeResult(success=True, output_key=node.output_key, output_value="success")
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
