"""Load deployment-only secrets before application settings are initialized."""

import os
from typing import Any

import boto3  # type: ignore[import-untyped]


class RuntimeSecretConfigurationError(RuntimeError):
    """Raised when the Lambda-only SSM secret configuration is incomplete."""


def ensure_openai_api_key() -> None:
    """Populate OPENAI_API_KEY from the configured SSM SecureString once per process."""
    if os.environ.get("OPENAI_API_KEY"):
        return

    parameter_name = os.environ.get("OPENAI_SSM_PARAMETER_NAME")
    if not parameter_name:
        raise RuntimeSecretConfigurationError("OPENAI_SSM_PARAMETER_NAME is not configured.")

    try:
        client: Any = boto3.client("ssm")
        response: dict[str, Any] = client.get_parameter(
            Name=parameter_name,
            WithDecryption=True,
        )
    except Exception as error:
        raise RuntimeSecretConfigurationError("Unable to load OPENAI_API_KEY from SSM.") from error

    value = response.get("Parameter", {}).get("Value")
    if not isinstance(value, str) or not value:
        raise RuntimeSecretConfigurationError("The configured SSM parameter has no usable value.")

    os.environ["OPENAI_API_KEY"] = value
