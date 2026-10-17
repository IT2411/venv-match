"""Unit tests for Phase 3 environment collectors."""

from dataclasses import dataclass

import pytest

from venv_match.collectors import (
    collect_environment_metadata,
    collect_packages_metadata,
    collect_platform_metadata,
    collect_python_metadata,
    collect_runtime_metadata,
    is_secret_variable_name,
)
from venv_match.exceptions import CollectionError


@dataclass
class _FakeDistribution:
    metadata: dict[str, str] | None
    version: str | None


def test_collect_python_metadata_structure() -> None:
    data = collect_python_metadata()
    assert isinstance(data["implementation"], str) and data["implementation"]
    assert isinstance(data["version"], str) and data["version"]
    assert isinstance(data["version_info"], list)
    assert len(data["version_info"]) == 3
    assert all(isinstance(part, int) for part in data["version_info"])
    assert isinstance(data["executable"], str) and data["executable"]
    assert isinstance(data["prefix"], str) and data["prefix"]
    assert isinstance(data["base_prefix"], str) and data["base_prefix"]
    assert isinstance(data["is_venv"], bool)


def test_collect_platform_metadata_structure() -> None:
    data = collect_platform_metadata()
    assert set(data.keys()) == {"system", "release", "machine"}
    for val in data.values():
        assert val is None or isinstance(val, str)


def test_collect_packages_normalizes_sorts_and_skips_malformed() -> None:
    fake_dists = [
        _FakeDistribution(metadata={"Name": "Zope.Interface"}, version="6.4.0"),
        _FakeDistribution(metadata={"Name": "My_Custom_Pkg"}, version="0.2.1"),
        _FakeDistribution(metadata={"Name": ""}, version="1.0.0"),
        _FakeDistribution(metadata=None, version=None),
        _FakeDistribution(metadata={"Name": "attrs"}, version="23.2.0"),
    ]
    result = collect_packages_metadata(distributions=fake_dists)  # type: ignore[arg-type]
    assert list(result.keys()) == ["attrs", "my-custom-pkg", "zope-interface"]
    assert result["zope-interface"] == "6.4.0"
    assert result["my-custom-pkg"] == "0.2.1"


def test_collect_runtime_metadata_structure() -> None:
    data = collect_runtime_metadata()
    assert set(data.keys()) == {"working_directory", "timezone", "locale"}
    assert isinstance(data["working_directory"], str) and data["working_directory"]


def test_environment_collector_empty_by_default() -> None:
    env = {"SECRET_TOKEN": "super-secret", "TZ": "UTC"}
    result = collect_environment_metadata(environ=env)
    assert result == {}


def test_environment_collector_presence_only_by_default() -> None:
    env = {"TZ": "UTC"}
    result = collect_environment_metadata(
        allowlist=["TZ", "MISSING_VAR"],
        include_values=False,
        environ=env,
    )
    assert result == {
        "MISSING_VAR": {"present": False},
        "TZ": {"present": True},
    }
    assert "value" not in result["TZ"]


def test_environment_collector_opt_in_values_and_secret_exclusion() -> None:
    env = {
        "TZ": "UTC",
        "GITHUB_TOKEN": "ghp_secret123",
        "DB_PASSWORD": "pw123",
        "MY_API_KEY": "key123",
        "SSH_PRIVATE_KEY": "priv123",
    }
    result = collect_environment_metadata(
        allowlist=[
            "TZ",
            "MISSING_VAR",
            "GITHUB_TOKEN",
            "DB_PASSWORD",
            "MY_API_KEY",
            "SSH_PRIVATE_KEY",
        ],
        include_values=True,
        environ=env,
    )
    assert result["TZ"] == {"present": True, "value": "UTC"}
    assert result["MISSING_VAR"] == {"present": False, "value": None}

    # Secret-like names must never have their values recorded even when include_values=True
    for secret_var in ("GITHUB_TOKEN", "DB_PASSWORD", "MY_API_KEY", "SSH_PRIVATE_KEY"):
        assert result[secret_var] == {"present": True}
        assert "value" not in result[secret_var]


def test_environment_collector_rejects_wildcards_and_empty_names() -> None:
    with pytest.raises(CollectionError, match="Wildcard"):
        collect_environment_metadata(allowlist=["AWS_*"], environ={})

    with pytest.raises(CollectionError, match="non-empty"):
        collect_environment_metadata(allowlist=["   "], environ={})


@pytest.mark.parametrize(
    ("var_name", "expected"),
    [
        ("API_TOKEN", True),
        ("MY_SECRET_VAL", True),
        ("USER_PASSWORD", True),
        ("ROOT_PASSWD", True),
        ("OPENAI_API_KEY", True),
        ("TLS_PRIVATE_KEY", True),
        ("PYTHONPATH", False),
        ("TZ", False),
        ("LANG", False),
    ],
)
def test_is_secret_variable_name(var_name: str, expected: bool) -> None:
    assert is_secret_variable_name(var_name) is expected
