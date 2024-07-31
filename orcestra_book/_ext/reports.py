#!/usr/bin/env python3
import os
import pathlib
import subprocess
from datetime import datetime
from docutils import nodes
from functools import lru_cache, partial

import yaml
from jinja2 import Template
from sphinx.util.docutils import SphinxRole


@lru_cache
def load_frontmatter(path, derive_flight=False):
    with open(path, "r") as fp:
        frontmatter = next(yaml.safe_load_all(fp))

    if derive_flight:
        takeoff = frontmatter["takeoff"]
        landing = frontmatter["landing"]

        frontmatter["expr_date"] = takeoff.strftime("%d %B %Y")
        frontmatter["expr_takeoff"] = takeoff.strftime("%X")
        frontmatter["expr_landing"] = landing.strftime("%X")
        frontmatter["expr_categories"] = map(
            lambda s: f"{{flight-cat}}`{s}`", frontmatter.get("categories", [])
        )

    return frontmatter


def collect_halo_refs(src, flight_id):
    refs =  ", ".join(
        f"[{t}](../{t}s/{flight_id})" for t in ("plan", "report")
        if (src / f"{t}s" / f"{flight_id}.md").is_file()
    )

    return f"{flight_id} ({refs})"


def write_flight_table(app):
    src = pathlib.Path(app.srcdir)
    flights = (src / "reports").glob("HALO-[0-9]*[a-z].md")

    func = partial(load_frontmatter, derive_flight=True)
    frontmatters = {fm["flight_id"]: fm for fm in map(func, sorted(flights))}

    for flight_id in frontmatters:
        frontmatters[flight_id]["expr_refs"] = collect_halo_refs(src, flight_id)

    with open(src / "_templates" / "operation_halo.md", "r") as fp:
        templ = fp.read()

    with open(src / "operation" / "halo.md", "w") as fp:
        t = Template(templ)
        fp.write(t.render(flights=frontmatters))


def write_ship_table(app):
    src = pathlib.Path(app.srcdir)
    reports = (src / "reports").glob("METEOR-[0-9]*.md")

    frontmatters = {fm["report_id"]: fm for fm in map(load_frontmatter, sorted(reports))}

    with open(src / "_templates" / "operation_rvmeteor.md", "r") as fp:
        templ = fp.read()

    with open(src / "operation" / "rvmeteor.md", "w") as fp:
        t = Template(templ)
        fp.write(t.render(reports=frontmatters))


def setup(app):
    app.connect("builder-inited", write_flight_table)
    app.connect("builder-inited", write_ship_table)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
