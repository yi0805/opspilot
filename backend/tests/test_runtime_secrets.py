import os
from unittest.mock import Mock, patch

import pytest

from app.core.runtime_secrets import (
    RuntimeSecretConfigurationError,
    ensure_openrouter_api_key,
)


def test_existing_openrouter_key_skips_ssm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "existing-key")
    monkeypatch.setenv("OPENROUTER_SSM_PARAMETER_NAME", "/opspilot/prod/openrouter-api-key")

    with patch("app.core.runtime_secrets.boto3.client") as client:
        ensure_openrouter_api_key()

    assert client.call_count == 0
    assert "existing-key" == os.environ["OPENROUTER_API_KEY"]


def test_missing_key_loads_configured_ssm_parameter(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_SSM_PARAMETER_NAME", "/opspilot/prod/openrouter-api-key")
    client = Mock()
    client.get_parameter.return_value = {"Parameter": {"Value": "loaded-key"}}

    with patch("app.core.runtime_secrets.boto3.client", return_value=client):
        ensure_openrouter_api_key()

    client.get_parameter.assert_called_once_with(
        Name="/opspilot/prod/openrouter-api-key",
        WithDecryption=True,
    )
    assert "loaded-key" == os.environ["OPENROUTER_API_KEY"]
    captured = capsys.readouterr()
    assert "loaded-key" not in captured.out
    assert "loaded-key" not in captured.err


def test_missing_parameter_name_fails_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_SSM_PARAMETER_NAME", raising=False)

    with pytest.raises(RuntimeSecretConfigurationError, match="OPENROUTER_SSM_PARAMETER_NAME"):
        ensure_openrouter_api_key()
