"""
=============================================================================
 MAIN ENTRY POINT
=============================================================================
This module is the entry point for running the application directly via module execution.
It allows users to start the app using `python -m cognitive_automator`.

Key Features:
1. Bootstraps the application when run from the command line.
2. Redirects execution to the primary main loop.

Think of this module as the ignition switch for the Cognitive Automator engine.
=============================================================================
"""

from cognitive_automator.main import main
main()
