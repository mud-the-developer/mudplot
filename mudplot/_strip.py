"""Dependency-free opt-in category strips; the legacy raw-x path stays intact."""

from .spec import StripSpec


def categorical_strip(layer):
    return layer.type == "stripplot" and (
        layer.strip is not None
        or layer.semantics is not None
        or layer.orient != "v"
        or layer.order is not None
        or layer.dodge is not None
        or layer.native_scale is not False
    )


def strip_option_issues(layer):
    config = layer.strip
    if config is None:
        return []
    if not isinstance(config, StripSpec):
        return ["strip must be a StripSpec"]
    issues = []
    if config.jitter_policy not in ("uniform", "none"):
        issues.append("strip jitter_policy must be uniform or none")
    if type(config.seed) is not int or not 0 <= config.seed <= 2**32 - 1:
        issues.append("strip seed must be an integer in [0, 2**32-1]")
    return issues
