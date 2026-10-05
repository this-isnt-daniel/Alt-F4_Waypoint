"""Data acquisition subpackage"""
from .manifest import generate_manifest
from .downloader import acquire_datasets

__all__ = ["generate_manifest", "acquire_datasets"]
