"""
Songmaker - A creativity tool for procedurally generating songs with rich metadata.

This module provides tools for creating songs with procedurally generated titles,
genres, descriptions and other attributes, with a focus on electronic music styles.
"""

from src.engine.songmaker.models.genre_graph import GenreGraph, GenreNode, genre_graph
from src.engine.songmaker.generators.title_generator import TitleGenerator
from src.engine.songmaker.generators.description_generator import DescriptionGenerator

__all__ = [
    'GenreGraph',
    'GenreNode', 
    'genre_graph',
    'TitleGenerator',
    'DescriptionGenerator'
] 