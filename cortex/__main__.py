"""
=============================================================================
 MAIN ENTRY POINT
=============================================================================
This module is the entry point for running the application directly via module execution.
It allows users to start the app using `python -m cortex`.

Key Features:
1. Bootstraps the application when run from the command line.
2. Redirects execution to the primary main loop.

Think of this module as the ignition switch for the Cortex engine.
=============================================================================
"""

from cortex.main import main
main()
