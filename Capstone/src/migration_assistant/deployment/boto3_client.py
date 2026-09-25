"""Thin boto3 wrapper used by deployment components."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import boto3


@dataclass(frozen=True, slots=True)
class Boto3ClientFactory:
	"""Centralized boto3 session/client construction.

	Keeping this wrapper small makes it easy to mock in tests and extend later
	with retries, custom endpoints, or shared session behavior.
	"""

	region_name: str | None = None
	profile_name: str | None = None
	cloudformation_endpoint_url: str | None = None

	@classmethod
	def from_state_config(cls, config: dict[str, Any] | None) -> "Boto3ClientFactory":
		raw = config if isinstance(config, dict) else {}
		aws = raw.get("aws") if isinstance(raw.get("aws"), dict) else {}
		deployment = (
			raw.get("deployment") if isinstance(raw.get("deployment"), dict) else {}
		)

		region_name = _first_non_empty(
			deployment.get("region_name"),
			aws.get("region_name"),
			raw.get("region_name"),
		)
		profile_name = _first_non_empty(
			deployment.get("profile_name"),
			aws.get("profile_name"),
			raw.get("aws_profile"),
		)
		endpoint_url = _first_non_empty(
			deployment.get("cloudformation_endpoint_url"),
			aws.get("cloudformation_endpoint_url"),
		)

		return cls(
			region_name=region_name,
			profile_name=profile_name,
			cloudformation_endpoint_url=endpoint_url,
		)

	def session(self) -> boto3.session.Session:
		kwargs: dict[str, Any] = {}
		if self.region_name:
			kwargs["region_name"] = self.region_name
		if self.profile_name:
			kwargs["profile_name"] = self.profile_name
		return boto3.session.Session(**kwargs)

	def client(self, service_name: str, *, endpoint_url: str | None = None) -> Any:
		session = self.session()
		resolved_endpoint = endpoint_url
		if resolved_endpoint is None and service_name == "cloudformation":
			resolved_endpoint = self.cloudformation_endpoint_url

		kwargs: dict[str, Any] = {}
		if resolved_endpoint:
			kwargs["endpoint_url"] = resolved_endpoint
		return session.client(service_name, **kwargs)

	def cloudformation_client(self) -> Any:
		return self.client("cloudformation")


def _first_non_empty(*values: Any) -> str | None:
	for value in values:
		if isinstance(value, str) and value.strip():
			return value.strip()
	return None
