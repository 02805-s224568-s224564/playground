import pytest


@pytest.fixture
def fake_repo(tmp_path):
    """A throwaway directory shaped like the repo, for figure-saving tests."""
    (tmp_path / "assets" / "figures").mkdir(parents=True)
    (tmp_path / "_includes").mkdir()
    (tmp_path / "_config.yml").write_text("title: test\n")
    return tmp_path


@pytest.fixture(scope="session")
def snapshot_dir():
    """data/raw/ with all snapshot files present and verified; skips when the course site is unreachable."""
    from marvel.data import SNAPSHOTS, SnapshotError, default_data_dir, ensure_snapshot

    try:
        for name in SNAPSHOTS:
            ensure_snapshot(name)
    except SnapshotError as err:
        pytest.skip(f"snapshot unavailable: {err}")
    return default_data_dir()
