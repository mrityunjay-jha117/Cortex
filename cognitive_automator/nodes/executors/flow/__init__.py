"""
=============================================================================
 FLOW EXECUTORS INITIALIZATION
=============================================================================
This module initializes the executors responsible for control flow logic.
It exposes nodes that manage branching, looping, and timing.

Key Features:
1. Groups control execution handlers into one location.
2. Allows easy registration of flow-based node types.

Think of this module as the dispatcher's desk for traffic control workers.
=============================================================================
"""

from .branch import *
from .compare import *
from .csv_data_loader import *
from .csv_writer import *
from .dynamic_iterate import *
from .for_loop import *
from .global_end import *
from .global_start import *
from .iterate import *
from .screenshotter import *
from .wait import *
from .write_file import *
