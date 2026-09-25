"""YAML serialization helpers for CloudFormation templates."""
from __future__ import annotations

from typing import Any

import yaml


def to_yaml(template: dict[str, Any]) -> str:
	"""Serialize an in-memory CloudFormation template to YAML text."""
	return yaml.safe_dump(template, sort_keys=False)
