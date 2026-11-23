"""Unreleased v2 C06: explicit frequency mass and selected-row percentages."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import mudplot as mp


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("artifacts/weighted_counts"))
    out = parser.parse_args().out
    out.mkdir(parents=True, exist_ok=True)
    data = {
        "condition": ["baseline", "baseline", "treated", "treated"],
        "cohort": ["u", "v", "u", "v"],
        "frequency": [1, 3, 2, 4],
    }
    for name, scope, scale in (
        ("weighted_counts", None, "linear"),
        ("category_log_counts", "category", "log"),
    ):
        plot = (
            mp.plot(data)
            .countplot(
                "condition",
                group="cohort",
                weights="frequency",
                stat="percent",
                normalize_scope=scope,
                stack=True,
                baseline=1 if scale == "log" else None,
                value_labels=True,
                label_format=".1f",
            )
            .labels(
                x="Condition",
                y="Frequency mass (%)" if scope else "Selected frequency mass (%)",
            )
            .legend(title="Cohort")
            .yscale(scale)
            .size(6, 3)
        )
        before = plot.to_json()
        for extension in ("png", "svg", "pdf"):
            plt.close(plot.save(out / f"{name}.{extension}", layout_policy="smart"))
        mp.save_spec(plot.spec, out / f"{name}.json")
        assert mp.load_spec(out / f"{name}.json") == plot.spec
        assert plot.to_json() == before and plot.spec.data.columns == data
    print(out)


if __name__ == "__main__":
    main()
