"""
=============================================================================
 __INIT__.PY (data_components)
=============================================================================
This module is a microservice component for data_components.
It was refactored to maintain modularity and separation of concerns.
=============================================================================
"""

from .csv_loader import CSVLoaderMixin
from .csv_writer import CSVWriterMixin
from .write_file import WriteFileMixin
from .file_drop import FileDropMixin

class DataBuilders(CSVLoaderMixin, CSVWriterMixin, WriteFileMixin, FileDropMixin):
    pass

__all__ = ["DataBuilders"]
