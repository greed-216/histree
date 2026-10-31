"""Import the CLI-named layout builder without executing its main entry point."""
import importlib.util
from pathlib import Path


def load_layout_builder():
    spec=importlib.util.spec_from_file_location('shiji_layout_builder',Path(__file__).with_name('build-shiji-reading-layout.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
