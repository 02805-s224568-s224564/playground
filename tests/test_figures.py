import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import pytest  # noqa: E402

from marvel import figures as mf  # noqa: E402


@pytest.fixture(autouse=True)
def _close_figures():
    yield
    plt.close("all")


def _fig():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3])
    return fig


def test_save_matplotlib_writes_png_and_snippet(fake_repo):
    snippet = mf.save_figure(
        _fig(), "degree", week=1, alt="Degree histogram", caption="Log-log axes.", wide=True, root=fake_repo
    )
    assert (fake_repo / "assets" / "figures" / "week1-degree.png").stat().st_size > 0
    assert snippet == (
        '{% include figure.html src="/assets/figures/week1-degree.png" '
        'alt="Degree histogram" caption="Log-log axes." wide=true %}'
    )


def test_minimal_snippet_omits_optional_params(fake_repo):
    snippet = mf.save_figure(_fig(), "x", week=2, alt="A", root=fake_repo)
    assert snippet == '{% include figure.html src="/assets/figures/week2-x.png" alt="A" %}'


def test_axes_accepted(fake_repo):
    fig, ax = plt.subplots()
    ax.plot([1])
    snippet = mf.save_figure(ax, "axes", week=1, alt="From axes", root=fake_repo)
    assert 'src="/assets/figures/week1-axes.png"' in snippet


def test_creates_figures_dir(tmp_path):
    mf.save_figure(_fig(), "x", week=1, alt="A", root=tmp_path)
    assert (tmp_path / "assets" / "figures" / "week1-x.png").exists()


def test_week_prefix_not_doubled():
    assert mf.figure_name(3, "week3-foo", "png") == "week3-foo.png"
    assert mf.figure_name(3, "foo", "html") == "week3-foo.html"


@pytest.mark.parametrize("bad", ["Foo", "a b", "-x", "", "x_y", "ä"])
def test_bad_slug_rejected(bad):
    with pytest.raises(ValueError, match="slug"):
        mf.figure_name(1, bad, "png")


def test_alt_required(fake_repo):
    with pytest.raises(ValueError, match="alt text is required"):
        mf.save_figure(_fig(), "x", week=1, alt="  ", root=fake_repo)


def test_double_quotes_switch_to_single_quotes(fake_repo):
    snippet = mf.save_figure(_fig(), "q", week=1, alt='He said "hi"', root=fake_repo)
    assert "alt='He said \"hi\"'" in snippet


def test_both_quote_kinds(fake_repo):
    snippet = mf.save_figure(_fig(), "q", week=1, alt="It's \"odd\"", root=fake_repo)
    assert "alt='It’s \"odd\"'" in snippet


def test_newline_rejected(fake_repo):
    with pytest.raises(ValueError, match="single line"):
        mf.save_figure(_fig(), "x", week=1, alt="two\nlines", root=fake_repo)


def test_unknown_object_rejected(fake_repo):
    with pytest.raises(TypeError):
        mf.save_figure(object(), "x", week=1, alt="A", root=fake_repo)


def test_plotly_figure_writes_html_and_iframe_snippet(fake_repo):
    go = pytest.importorskip("plotly.graph_objects")
    fig = go.Figure(data=[go.Scatter(x=[1, 2], y=[3, 4])])
    snippet = mf.save_figure(fig, "explorer", week=2, alt="Explorer", height=500, wide=True, root=fake_repo)
    path = fake_repo / "assets" / "figures" / "week2-explorer.html"
    assert "cdn.plot.ly" in path.read_text()
    assert snippet == (
        '{% include interactive.html src="/assets/figures/week2-explorer.html" alt="Explorer" height=500 wide=true %}'
    )


def test_apply_style_sets_defaults():
    mf.apply_style()
    assert matplotlib.rcParams["savefig.dpi"] == 150
    assert matplotlib.rcParams["axes.spines.top"] is False
    assert matplotlib.rcParams["axes.prop_cycle"].by_key()["color"][0] == mf.ACCENT
