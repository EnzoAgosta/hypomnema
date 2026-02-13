"""TMX deserialization components.

Provides deserializer infrastructure for converting XML to Python objects.

Classes:
    BaseElementDeserializer: Abstract base class for element deserializers.
    Deserializer: Orchestrator that dispatches elements to handlers.

Handlers:
    NoteDeserializer, PropDeserializer, HeaderDeserializer, TuDeserializer,
    TuvDeserializer, BptDeserializer, EptDeserializer, ItDeserializer,
    PhDeserializer, SubDeserializer, HiDeserializer, TmxDeserializer
"""

from .base import BaseElementDeserializer
from .deserializer import Deserializer
from .handlers import (
  BptDeserializer,
  EptDeserializer,
  HeaderDeserializer,
  HiDeserializer,
  ItDeserializer,
  NoteDeserializer,
  PhDeserializer,
  PropDeserializer,
  SubDeserializer,
  TmxDeserializer,
  TuDeserializer,
  TuvDeserializer,
)

__all__ = [
  "BaseElementDeserializer",
  "BptDeserializer",
  "Deserializer",
  "EptDeserializer",
  "HeaderDeserializer",
  "HiDeserializer",
  "ItDeserializer",
  "NoteDeserializer",
  "PhDeserializer",
  "PropDeserializer",
  "SubDeserializer",
  "TmxDeserializer",
  "TuDeserializer",
  "TuvDeserializer",
]
