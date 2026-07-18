
import base64
from io import BytesIO
from PIL import Image
from cognitive_automator.llm.structured import _tile_image_if_large

def test_tiling_threshold_1080p():
    # Create a 1920x1080 image
    img = Image.new('RGB', (1920, 1080), color = 'red')
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64_data = base64.b64encode(buf.getvalue()).decode()
    
    # Previously (max_dimension=1500), this would result in 3 tiles
    # Now (max_dimension=3000), it should be 1
    tiles = _tile_image_if_large(b64_data)
    assert len(tiles) == 1
    assert tiles[0] == b64_data

def test_tiling_threshold_4k():
    # Create a 4K image (3840x2160)
    img = Image.new('RGB', (3840, 2160), color = 'blue')
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64_data = base64.b64encode(buf.getvalue()).decode()
    
    # This should still be tiled because 3840 > 3000
    tiles = _tile_image_if_large(b64_data)
    assert len(tiles) > 1
    # First tile is always the resized global context
    assert len(tiles) >= 2
