from .base import *
def execute_wait(node: WaitNode, context: dict[str, Any],
                 abort_signal: Callable[[], bool] | None = None,
                 emit_info: Callable[[str], None] | None = None,
                 dev_mode: bool = False,
                 llm_config: LLMConfig | None = None) -> NodeResult:
    try:
        if node.wait_for_image_b64:
            import base64
            import tempfile
            import os
            
            log.info("WaitNode: Waiting for image to appear (timeout=%.1fs)", node.timeout_seconds)
            
            img_data = base64.b64decode(node.wait_for_image_b64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(img_data)
                tmp_path = f.name
            
            deadline = time.monotonic() + node.timeout_seconds
            found = False
            try:
                while time.monotonic() < deadline:
                    if abort_signal and abort_signal():
                        return NodeResult(success=False, error="Aborted")
                    loc = pyautogui.locateOnScreen(tmp_path, confidence=node.wait_confidence,
                                                    grayscale=False)
                    if loc:
                        log.info("WaitNode: Image found successfully.")
                        found = True
                        break
                    time.sleep(node.poll_interval)
                
                if found:
                    return NodeResult(success=True)

                # --- Fallback for WaitNode ---
                # Check if LocateElement style fallback should be tried here too
                # For now, let's keep it consistent if the user enables it on a linked LocateNode
                # but WaitNode doesn't have a 'use_fallback' field yet in graph_model.
                # If we want WaitNode to support it, we'd need to add the field there too.
                # However, if LocateElement is used as a 'wait' (with its timeout), it already has it.

                return NodeResult(success=False, error="Timed out waiting for image")
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
        else:
            remaining = node.static_seconds or 1.0
            log.info("WaitNode: Sleeping for %.1f seconds", remaining)
            while remaining > 0:
                if abort_signal and abort_signal():
                    return NodeResult(success=False, error="Aborted")
                step = min(remaining, 0.1)
                time.sleep(step)
                remaining -= step
            return NodeResult(success=True)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))


def execute_branch(node: BranchNode, context: dict[str, Any]) -> NodeResult:
    value = context.get(node.condition_key)
    if value is None:
        return NodeResult(success=False,
                          error=f"BranchNode: condition key '{node.condition_key}' not in context")
    is_true = bool(value) if not isinstance(value, dict) else bool(value.get("result", False))
    return NodeResult(success=True, next_edge=EdgeLabel.TRUE if is_true else EdgeLabel.FALSE)


def execute_iterate(node: IterateNode, context: dict[str, Any]) -> NodeResult:
    """
    Manages loop state in the context under '_iterate_{node_id}'.
    Returns LOOP_BODY edge while items remain, LOOP_END when exhausted.
    """
    state_key = f"_iterate_{node.id}"
    state = context.get(state_key, {"index": 0, "items": None})

    if state["items"] is None:
        # First call: load items
        if node.csv_file_path:
            items = _load_csv_column(node.csv_file_path, node.csv_column)
        else:
            items = list(node.items)
        state["items"] = items
        state["index"] = 0

    items: list[str] = state["items"]
    idx: int = state["index"]

    if idx >= len(items):
        # Reset state for potential re-run
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    current_item = items[idx]
    state["index"] = idx + 1
    context[state_key] = state

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_item,
    )


def execute_dynamic_iterate(node: DynamicIterateNode, context: dict[str, Any]) -> NodeResult:
    """
    Iterates over a runtime list in context[source_key].
    Items can be (cx, cy) tuples (from LocateAll) or strings (from OCR/LLM).
    Returns LOOP_BODY with the current item, LOOP_END when exhausted.
    """
    state_key = f"_dyn_iterate_{node.id}"
    state = context.get(state_key, {"index": 0, "items": None})

    if state["items"] is None:
        raw = context.get(node.source_key, [])
        state["items"] = list(raw) if isinstance(raw, (list, tuple)) else [raw]
        state["index"] = 0

    items: list = state["items"]
    idx: int = state["index"]

    if idx >= len(items):
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    current_item = items[idx]
    state["index"] = idx + 1
    context[state_key] = state

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_item,
    )


def execute_for_loop(node: ForLoopNode, context: dict[str, Any], graph: ActionGraph) -> NodeResult:
    """
    C++ style counter loop: for (int i = start; i < end; i += step)
    Data is resolved from incoming DATA_BIND edges.
    """
    state_key = f"_for_{node.id}"
    current_val = context.get(state_key)

    # Resolve data sources from graph edges
    data_sources = [e.source_id for e in graph.edges if e.target_id == node.id and e.label == EdgeLabel.DATA_BIND]
    
    # Cap the loop end based on data length if sources exist
    loop_end = node.end
    for src_id in data_sources:
        src_node = graph.nodes.get(src_id)
        if src_node and hasattr(src_node, "output_key"):
            key = src_node.output_key
            if key in context:
                data = context[key]
                if isinstance(data, (list, dict)):
                    loop_end = min(loop_end, len(data))

    if current_val is None:
        current_val = node.start
    
    # Condition check (continues while i < loop_end)
    should_continue = False
    if node.step > 0:
        should_continue = current_val < loop_end
    else:
        should_continue = current_val > loop_end

    if not should_continue:
        context.pop(state_key, None)
        context.pop(node.output_key, None)  # Scope isolation: cleanup iterator
        return NodeResult(success=True, next_edge=EdgeLabel.LOOP_END)

    # Prepare for next pass
    next_val = current_val + node.step
    context[state_key] = next_val

    return NodeResult(
        success=True,
        next_edge=EdgeLabel.LOOP_BODY,
        output_key=node.output_key,
        output_value=current_val,
    )


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


def execute_compare(node: CompareNode, context: dict[str, Any]) -> NodeResult:
    """
    Resolves both operands from context (supports {{key}} templates),
    applies the operator, and returns TRUE or FALSE edge.
    """
    def _resolve(template: str) -> str:
        from cognitive_automator.llm.templates import render_prompt
        return render_prompt(template, context)

    left = _resolve(node.left_operand)
    right = _resolve(node.right_operand)

    op = node.operator
    cs = node.case_sensitive

    try:
        if op == CompareOp.IS_EMPTY:
            passed = left.strip() == ""
        elif op == CompareOp.IS_NOT_EMPTY:
            passed = left.strip() != ""
        elif op in (CompareOp.NUM_GT, CompareOp.NUM_LT,
                    CompareOp.NUM_GTE, CompareOp.NUM_LTE, CompareOp.NUM_EQUALS):
            lv, rv = float(left), float(right)
            passed = {
                CompareOp.NUM_GT:     lv > rv,
                CompareOp.NUM_LT:     lv < rv,
                CompareOp.NUM_GTE:    lv >= rv,
                CompareOp.NUM_LTE:    lv <= rv,
                CompareOp.NUM_EQUALS: lv == rv,
            }[op]
        else:
            # String operators
            left_val, right_val = (left, right) if cs else (left.lower(), right.lower())
            passed = {
                CompareOp.EQUALS:      left_val == right_val,
                CompareOp.NOT_EQUALS:  left_val != right_val,
                CompareOp.CONTAINS:    right_val in left_val,
                CompareOp.NOT_CONTAINS: right_val not in left_val,
                CompareOp.STARTS_WITH: left_val.startswith(right_val),
                CompareOp.ENDS_WITH:   left_val.endswith(right_val),
            }[op]
    except (ValueError, KeyError) as exc:
        return NodeResult(success=False, error=f"CompareNode error: {exc}")

    log.debug("CompareNode: %r %s %r → %s", left, op.value, right, passed)
    return NodeResult(success=True, next_edge=EdgeLabel.TRUE if passed else EdgeLabel.FALSE)


def execute_global_start(node: GlobalStartNode, context: dict[str, Any]) -> NodeResult:
    """Entry point marker. Does nothing but pass flow."""
    log.info("Automation started via GlobalStartNode")
    return NodeResult(success=True)


def execute_global_end(node: GlobalEndNode, context: dict[str, Any]) -> NodeResult:
    """Exit point marker. Signals completion."""
    log.info("Automation completed via GlobalEndNode")
    return NodeResult(success=True)


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


def execute_screenshotter(node: ScreenshotterNode, context: dict[str, Any]) -> NodeResult:
    """Captures a sequence of screenshots by scrolling and optionally performs actions on detection."""
    import base64
    import tempfile
    import os
    from io import BytesIO
    from PIL import ImageChops  # type: ignore
    
    tmp_path = None
    try:
        images: list[str] = []
        last_img_hash = None
        
        log.info("Screenshotter: mode=%s, detection=%s", node.mode, node.detection_mode)
        
        # Prepare detection image if needed
        if node.detection_mode != DetectionMode.NONE and node.reference_image_b64:
            img_data = base64.b64decode(node.reference_image_b64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(img_data)
                tmp_path = f.name

        # Max limit to prevent infinite loops in UNTIL_END mode
        max_limit = node.n_times if node.mode == ScreenshotMode.N_TIMES else 50
        
        for i in range(max_limit):
            # 1. Capture current screen
            img = pyautogui.screenshot()
            
            # 2. Compare if mode is UNTIL_END
            if node.mode == ScreenshotMode.UNTIL_END:
                if last_img_hash:
                    diff = ImageChops.difference(img, last_img_hash)
                    if not diff.getbbox():
                        log.info("Screenshotter: Page end reached")
                        break
                last_img_hash = img

            # 3. Optional Detection and Action
            if tmp_path:
                try:
                    if node.detection_mode == DetectionMode.SINGLE:
                        loc = pyautogui.locateOnScreen(tmp_path, confidence=node.confidence, grayscale=node.grayscale)
                        if loc:
                            cx, cy = pyautogui.center(loc)
                            pyautogui.click(cx + node.x_offset, cy + node.y_offset)
                            log.info("Screenshotter: Clicked match at (%d, %d)", cx + node.x_offset, cy + node.y_offset)
                            time.sleep(node.wait_after_click)
                    elif node.detection_mode == DetectionMode.MULTIPLE:
                        # Robust "Click each as it appears": re-scan after each click
                        for _ in range(20): # Safety limit for one page
                            loc = pyautogui.locateOnScreen(tmp_path, confidence=node.confidence, grayscale=node.grayscale)
                            if not loc:
                                break
                            cx, cy = pyautogui.center(loc)
                            pyautogui.click(cx + node.x_offset, cy + node.y_offset)
                            log.info("Screenshotter: Clicked match at (%d, %d)", cx + node.x_offset, cy + node.y_offset)
                            time.sleep(node.wait_after_click)
                            # Small extra wait to let UI settle
                            time.sleep(0.2)
                except Exception as detect_exc:
                    log.warning("Screenshotter: Detection error in step %d: %s", i, detect_exc)

            # 4. Store base64
            buf = BytesIO()
            img.save(buf, format="PNG")
            images.append(base64.b64encode(buf.getvalue()).decode())
            
            # 5. Scroll and wait
            log.debug("Screenshotter: step %d, scrolling %d", i+1, node.scroll_amount)
            pyautogui.scroll(node.scroll_amount)
            time.sleep(max(node.wait_per_scroll, 0.2))

        log.info("Screenshotter: captured %d images", len(images))
        return NodeResult(success=True, output_key=node.output_key, output_value=images)
    except Exception as exc:
        return NodeResult(success=False, error=str(exc))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


def _load_csv_column(path: str, column: str) -> list[str]:
    if path.lower().endswith((".xlsx", ".xls")):
        return _load_excel_column(path, column)
    items: list[str] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if column and column in row:
                items.append(row[column])
            elif not column:
                items.append(next(iter(row.values()), ""))
    return items


def _load_excel_column(path: str, column: str) -> list[str]:
    try:
        import openpyxl  # type: ignore
    except ImportError:
        raise ImportError(
            "openpyxl is required to read Excel files. Install it with: pip install openpyxl"
        )
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    items: list[str] = []
    headers: list[str] = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):  # type: ignore[union-attr]
        if i == 0:
            headers = [str(c) if c is not None else "" for c in row]
            continue
        if column and column in headers:
            val = row[headers.index(column)]
        elif not column and row:
            val = row[0]
        else:
            continue
        items.append(str(val) if val is not None else "")
    wb.close()
    return items
