"""Configuration objects for environment snapshot collection."""

from dataclasses import dataclass

from venv_match.collectors.environment import validate_env_var_name


@dataclass(frozen=True)
class CaptureConfig:
    """Configuration controlling which environment sections and variables are captured."""

    include_packages: bool = True
    include_platform: bool = True
    include_runtime: bool = True
    env_vars: tuple[str, ...] = ()
    include_env_values: bool = False
    strict_optional_collectors: bool = False

    def __post_init__(self) -> None:
        normalized_vars = tuple(
            sorted({validate_env_var_name(name) for name in self.env_vars})
        )
        object.__setattr__(self, "env_vars", normalized_vars)
