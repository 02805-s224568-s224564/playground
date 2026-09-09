"""Save a figure into assets/figures/ and get back the Liquid include for the post.

    from marvel import apply_style, save_figure

    apply_style()                                    # once per notebook
    fig, ax = plt.subplots()
    ...
    print(save_figure(fig, "degree-distribution", week=1,
                      alt="Log-log degree distribution of the 303-hero graph",
                      caption="The tail is heavier than a random graph's.",
                      wide=True))

    {% include figure.html src="/assets/figures/week1-degree-distribution.png" alt="..." caption="..." wide=true %}

Paste that line into the post. Markdown image syntax is deliberately not
offered: the site is served under /playground, and only the include routes the
path through relative_url. A plotly figure is written as a standalone HTML file
and the snippet uses interactive.html (an iframe) instead.
"""

from __future__ import annotations

import re
from pathlib import Path

__all__ = ["ACCENT", "PALETTE", "apply_style", "figure_name", "figures_dir", "save_figure"]

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")

ACCENT = "#c0341c"  # the site's accent colour, see assets/css/main.css
PALETTE = [ACCENT, "#1f5f8b", "#3a7d44", "#8a5a00", "#6c4a8a", "#555555"]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def figures_dir(root: Path | str | None = None) -> Path:
    return Path(root or repo_root()) / "assets" / "figures"


def apply_style() -> None:
    """Consistent matplotlib defaults for every post: white ground, light grid, site palette."""
    import matplotlib as mpl
    from cycler import cycler

    mpl.rcParams.update(
        {
            "figure.figsize": (8, 5),
            "figure.dpi": 100,
            "figure.facecolor": "white",
            "savefig.dpi": 150,
            "savefig.bbox": "tight",
            "savefig.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": "#444444",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.axisbelow": True,
            "grid.alpha": 0.3,
            "grid.linestyle": "-",
            "axes.titlesize": 13,
            "axes.titleweight": "semibold",
            "axes.labelsize": 11,
            "font.size": 11,
            "legend.frameon": False,
            "axes.prop_cycle": cycler(color=PALETTE),
        }
    )


def figure_name(week: int, slug: str, ext: str) -> str:
    """week<N>-<slug>.<ext>; a slug that already starts with week<N>- is not doubled."""
    week = int(week)
    if week < 1:
        raise ValueError("week must be a positive integer")
    prefix = f"week{week}-"
    if slug.startswith(prefix):
        slug = slug[len(prefix):]
    if not SLUG_RE.match(slug):
        raise ValueError(
            f"slug {slug!r} must be lowercase letters, digits and hyphens (pattern {SLUG_RE.pattern})"
        )
    return f"{prefix}{slug}.{ext}"


def _liquid_str(value: str, param: str) -> str:
    """Quote a value for a Liquid include parameter."""
    if "\n" in value or "\r" in value:
        raise ValueError(f"{param} must be a single line")
    if '"' not in value:
        return f'"{value}"'
    if "'" not in value:
        return f"'{value}'"
    return "'" + value.replace("'", "’") + "'"


def _resolve(fig):
    """Return ("matplotlib" | "plotly", figure), unwrapping Axes."""
    module = type(fig).__module__ or ""
    if module.startswith("plotly"):
        return "plotly", fig
    try:
        from matplotlib.axes import Axes
        from matplotlib.figure import Figure
    except ImportError:  # pragma: no cover
        raise TypeError("matplotlib is not installed and this is not a plotly figure") from None
    if isinstance(fig, Axes):
        fig = fig.figure
    if isinstance(fig, Figure):
        return "matplotlib", fig
    raise TypeError(f"save_figure expects a matplotlib Figure or Axes, or a plotly Figure; got {type(fig).__name__}")


def save_figure(
    fig,
    slug: str,
    *,
    week: int,
    alt: str,
    caption: str | None = None,
    wide: bool = False,
    dpi: int = 150,
    height: int = 480,
    root: Path | str | None = None,
) -> str:
    """Write the figure to assets/figures/week<N>-<slug>.{png,html} and return the include line.

    alt is required: it is what a screen reader and the examiner on a phone get.
    caption is markdown. wide=True lets the figure break out of the text column.
    height (px) applies to interactive figures only.
    """
    if not alt or not alt.strip():
        raise ValueError("alt text is required: describe what the figure shows for a reader who cannot see it")

    kind, fig = _resolve(fig)
    ext = "png" if kind == "matplotlib" else "html"
    name = figure_name(week, slug, ext)
    out_dir = figures_dir(root)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name

    if kind == "matplotlib":
        fig.savefig(path, dpi=dpi, bbox_inches="tight")
        include = "figure.html"
    else:
        fig.write_html(str(path), include_plotlyjs="cdn", full_html=True, config={"responsive": True})
        include = "interactive.html"

    parts = [f"src={_liquid_str('/assets/figures/' + name, 'src')}", f"alt={_liquid_str(alt.strip(), 'alt')}"]
    if caption and caption.strip():
        parts.append(f"caption={_liquid_str(caption.strip(), 'caption')}")
    if kind == "plotly":
        parts.append(f"height={int(height)}")
    if wide:
        parts.append("wide=true")
    return "{% include " + include + " " + " ".join(parts) + " %}"
