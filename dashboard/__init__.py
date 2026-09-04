"""mudplot dashboard — the human-facing counterpart to the engine.

Separate from the ``mudplot`` engine package on purpose: the engine stays
pure/agent-facing (JSON actions, capabilities, schema), while everything here
is UI/human-facing and free to depend on ``mudplot[render]`` and the
filesystem. See ``dashboard/README.md`` for the roadmap (static site now,
interactive Rust/htmx editor later — both drive the same engine Store).
"""
