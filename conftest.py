"""
conftest.py — project-level pytest configuration.
Adds src/ to sys.path so that all tests can import knowledge_base,
inference_engine, and analyzer without any relative path hacks.
"""
import sys
from pathlib import Path

# Insert src/ at the front of the module search path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

