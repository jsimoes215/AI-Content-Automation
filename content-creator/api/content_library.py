"""
Wrapper module to handle content-library directory with dash in name
"""
import sys
import importlib.util
from pathlib import Path

# Load the library_manager module directly
library_manager_path = Path(__file__).parent / "content-library" / "library_manager.py"
spec = importlib.util.spec_from_file_location("library_manager_module", library_manager_path)
library_manager_module = importlib.util.module_from_spec(spec)
sys.modules["library_manager_module"] = library_manager_module
spec.loader.exec_module(library_manager_module)

# Export the classes
ContentLibraryManager = library_manager_module.ContentLibraryManager
SceneMetadata = library_manager_module.SceneMetadata
SearchQuery = library_manager_module.SearchQuery