from ..base import *

def execute_csv_data_loader(node: CSVDataLoaderNode, context: dict[str, Any]) -> NodeResult:
    """Loads CSV into list of dicts."""
    try:
        import csv
        if not node.file_path:
            raise ValueError("CSVDataLoader: file_path is empty")
            
        with open(node.file_path, newline="", encoding="utf-8-sig") as f:
            # Use a list to strip headers immediately
            reader = csv.reader(f)
            headers = [h.strip() for h in next(reader)]
            
            data = []
            for row in reader:
                # Zip headers with stripped values
                data.append({headers[i]: str(row[i]).strip() for i in range(len(headers)) if i < len(row)})
            
        log.info("CSVDataLoader: Loaded %d rows from %s", len(data), node.file_path)
        log.info("CSV Attributes found: %s", ", ".join(headers))
        return NodeResult(success=True, output_key=node.output_key, output_value=data)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
