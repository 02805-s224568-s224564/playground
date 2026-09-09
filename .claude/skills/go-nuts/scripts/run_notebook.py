#!/usr/bin/env python
"""Execute notebooks headlessly so a broken cell or a stale figure is caught before publishing.

    run_notebook.py notebooks/week2-*.ipynb
    run_notebook.py notebooks/week2-models.ipynb --save-to /tmp/executed

Runs each notebook top to bottom with its own directory as the working
directory, exactly as JupyterLab would. Outputs are not written back to the
notebook (nbstripout would strip them anyway); figures the notebook saves into
assets/figures/ are regenerated as a side effect, which is the point.

Exit 1 if any notebook fails.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

from _common import REPO_ROOT, die, rel

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _failing_cell(nb):
    for index, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            continue
        for output in cell.get("outputs", []):
            if output.get("output_type") == "error":
                return index, cell, output
    return None, None, None


def run(path: Path, timeout: int, kernel: str, save_to: Path | None) -> bool:
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError
    from jupyter_client.kernelspec import NoSuchKernel

    nb = nbformat.read(path, as_version=4)
    started = time.monotonic()
    print(f"==> {rel(path)} (kernel {kernel}, timeout {timeout}s per cell)")

    def client(name):
        return NotebookClient(
            nb,
            timeout=timeout,
            kernel_name=name,
            allow_errors=False,
            resources={"metadata": {"path": str(path.parent)}},
        )

    try:
        try:
            client(kernel).execute()
        except NoSuchKernel:
            if kernel == "python3":
                raise
            print(f"    kernel {kernel!r} not found, retrying with python3", file=sys.stderr)
            client("python3").execute()
    except NoSuchKernel as err:
        die(f"no usable Jupyter kernel ({err}); run `jupyter kernelspec list` and pass --kernel")
    except CellExecutionError:
        index, cell, output = _failing_cell(nb)
        print(f"FAILED  {rel(path)}: cell {index} raised {output.get('ename')}: {output.get('evalue')}")
        source_head = "\n".join(cell.source.splitlines()[:3])
        print("    --- cell source (first lines) ---")
        print("    " + source_head.replace("\n", "\n    "))
        traceback = [ANSI.sub("", line) for line in output.get("traceback", [])]
        tail = "\n".join(traceback)[-1500:]
        print("    --- traceback (tail) ---")
        print("    " + tail.replace("\n", "\n    "))
        return False
    except Exception as err:  # dead kernel, timeout, etc.
        print(f"FAILED  {rel(path)}: {type(err).__name__}: {err}")
        return False
    finally:
        if save_to is not None:
            save_to.mkdir(parents=True, exist_ok=True)
            out = save_to / (path.stem + ".executed.ipynb")
            nbformat.write(nb, out)
            print(f"    executed copy: {out}")

    print(f"ok      {rel(path)} ran clean in {time.monotonic() - started:.0f}s")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("notebooks", nargs="+", type=Path)
    parser.add_argument("--timeout", type=int, default=600, help="seconds per cell (default 600)")
    parser.add_argument("--kernel", default="python3")
    parser.add_argument("--save-to", type=Path, help="directory for executed copies (default: none)")
    args = parser.parse_args(argv)

    os.environ.setdefault("MPLBACKEND", "Agg")
    paths = [p if p.is_absolute() else REPO_ROOT / p for p in args.notebooks]
    missing = [p for p in paths if not p.exists()]
    if missing:
        die("not found: " + ", ".join(rel(p) for p in missing))

    results = [run(p, args.timeout, args.kernel, args.save_to) for p in paths]
    if all(results):
        print("all notebooks ran clean; assets/figures/ has been regenerated from them")
        return 0
    print(f"{results.count(False)} of {len(results)} notebook(s) failed")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
