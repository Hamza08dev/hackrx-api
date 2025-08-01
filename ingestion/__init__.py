"""Ingestion module for document loading and text extraction."""

from .document_loader import extract_text_from_file, is_supported_file, get_supported_extensions

__all__ = ['extract_text_from_file', 'is_supported_file', 'get_supported_extensions']