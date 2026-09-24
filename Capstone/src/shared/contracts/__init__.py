"""Typed contracts shared by source and target pipelines."""

from .models import AnalysisOutput, DiscoveryOutput, GenerationOutput, MappingOutput
from .spec import (
    UnsupportedSpecVersionError,
    validate_migration_spec_file,
    validate_migration_spec_payload,
)

__all__ = [
    "AnalysisOutput",
    "DiscoveryOutput",
    "GenerationOutput",
    "MappingOutput",
    "UnsupportedSpecVersionError",
    "validate_migration_spec_file",
    "validate_migration_spec_payload",
]
