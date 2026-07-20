"""
=============================================================================
 LOCATE_CORE_FALLBACK.PY (vision_components)
=============================================================================
This module is a microservice component for vision_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .base import *
from typing import Callable
from .locate_fallback import run_vlm_fallback

def handle_locate_fallback(node: LocateElementNode, haystack, v_left, v_top, v_width, v_height,
                           emit_info: Callable[[str], None] | None, dev_mode: bool, llm_config: LLMConfig | None) -> NodeResult:
    if not node.use_fallback or dev_mode or not llm_config:
        return NodeResult(success=False, error=f"Element not found within {node.timeout_seconds}s")
        
    prompt = node.fallback_prompt or f"detect {node.label or 'the element'}"
    provider = node.fallback_provider_override or llm_config.fallback_provider
    model = node.fallback_model_override or llm_config.fallback_model
    
    log.info("LocateElement primary failed. Attempting AI Fallback [v3] [Provider: %s, Model: %s] with prompt: '%s'", 
             provider, model, prompt)
    
    from PIL import ImageGrab
    import io
    if not haystack:
        haystack = ImageGrab.grab(all_screens=True)
    
    sw_phys, sh_phys = haystack.size
    buffered = BytesIO()
    haystack.save(buffered, format="PNG")
    screenshot_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    try:
        fb_data = run_vlm_fallback(screenshot_b64, prompt, provider, model, llm_config)
        if fb_data:
            nx_click, ny_click = fb_data["click"]
            nx_center, ny_center = fb_data["center"]
            xmin, ymin, xmax, ymax = fb_data["bbox_raw"]
            
            log.debug("AI Fallback RAW: click=%s center=%s bbox=%s", 
                      (nx_click, ny_click), (nx_center, ny_center), fb_data["bbox_raw"])

            cx = int(v_left + (nx_click * v_width / 1000.0))
            cy = int(v_top + (ny_click * v_height / 1000.0))
            
            healed_flag = False
            
            if node.auto_heal:
                log.info("Self-healing: Updating node with AI bounding box...")
                try:
                    node.x_coord = int(v_left + (nx_center * v_width / 1000.0))
                    node.y_coord = int(v_top + (ny_center * v_height / 1000.0))
                    
                    left_p = int(xmin * sw_phys / 1000.0)
                    top_p = int(ymin * sh_phys / 1000.0)
                    right_p = int(xmax * sw_phys / 1000.0)
                    bottom_p = int(ymax * sh_phys / 1000.0)
                    
                    new_patch = haystack.crop((max(0, left_p-2), max(0, top_p-2), 
                                               min(sw_phys, right_p+2), min(sh_phys, bottom_p+2)))
                    
                    patch_buf = BytesIO()
                    new_patch.save(patch_buf, format="PNG")
                    node.reference_image_b64 = base64.b64encode(patch_buf.getvalue()).decode("utf-8")
                    
                    log.info("Self-healing SUCCESSFUL: Node healed at logical (%d, %d).", 
                             node.x_coord, node.y_coord)
                    healed_flag = True
                except Exception as heal_exc:
                    log.error("Self-healing FAILED: %s", heal_exc)

            cx += node.x_offset
            cy += node.y_offset

            log.info("AI Fallback SUCCESS: Element found. Final logical coordinates at (%d, %d).", cx, cy)
            if emit_info:
                emit_info("AI Fallback completed successfully.")
            return NodeResult(success=True, output_key=node.output_key, output_value=(cx, cy), healed=healed_flag)
        else:
            log.warning("AI Fallback FAILED: AI could not locate the element.")
    except Exception as fb_exc:
        log.error("AI Fallback CRITICAL ERROR: %s", fb_exc, exc_info=True)

    return NodeResult(success=False, error=f"Element not found within {node.timeout_seconds}s")
