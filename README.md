# qPilot

Open qPCR analysis that reads the instrument's raw curves, analyses every plate the same way, and shows which of your analysis choices could change your conclusion.

**For research use only. Not for clinical or diagnostic use.**

> **Project status: early scaffold (v0.1.0).** This repository currently contains the package
> skeleton, the data contracts every layer is built against, a command-line shell, contract
> fixtures for the demo study and the quality tooling. The analysis engine, web app, MCP server
> and AI layer described under [Planned features](#planned-features) are **not implemented yet**.
> The CLI installs and runs but has no sub-commands registered.

## Why

A qPCR result such as "ODC1 is 3.6-fold up in MYCN-high tumours" depends on choices the analyst
makes along the way: which reference genes to normalise against, where to cut the groups, what to
do with undetermined wells. qPilot's aim is to make those choices explicit, re-run the analysis
under every reasonable alternative, and tell you which conclusions survive and which flip.

## What is here today

- **Data contracts** (`qpilot/schemas.py`): pydantic v2 models for contrasts, geNorm reference-gene
  stability, robustness across an analysis grid, ordinal confidence grades with every downgrade
  named, Decision Cards (a choice that could change a conclusion, with options and evidence),
  a hash-chained decision log entry, and the `DecisionSpace` / `StudyStoreAPI` protocols that
  domain plugins and the store implement.
- **Contract fixtures** (`tests/fixtures/`): the expected results, Decision Cards and 601 citable
  facts for the 64-plate Vermeulen neuroblastoma benchmark (24,576 reactions, 366 samples,
  58 genes), plus a small real RDML file and an XXE regression file.
- **CLI shell** (`qpilot`, `python -m qpilot`): an `argparse` dispatcher with a simple
  registration format so each area adds commands in its own module.
- **Tests** that check the contracts accept valid data and reject invalid data, that the fixtures
  are internally consistent (every fact's value matches the field it points to, every conclusion
  follows the stated conclusion rule, fold changes match their log2 values and confidence
  intervals, recommended options reproduce the primary analysis), and that the CLI behaves.
- **Quality rails**: ruff (lint + format), mypy (strict), pytest with network access disabled,
  pre-commit (ruff, gitleaks), pip-audit, Dependabot and GitHub Actions CI.

## Planned features

These are the design goals the contracts were written for. None of them is implemented yet.

- Hardened RDML loading (no external entities, DTDs or network access) and a pinned demo-dataset
  download.
- Per-well amplification efficiency with LinRegPCR (via vendored rdmlpython) and geNorm reference
  gene selection.
- A robustness grid over analysis choices, with Decision Cards ranked by how many conclusions they
  can flip.
- Confidence grades (High / Moderate / Low / Very low) with named reasons, never a probability.
- A tamper-evident, hash-chained decision record.
- A local Gradio app, an MCP server, and optional model-written explanations that may only quote
  numbers by fact id.

## Stack

Python 3.11+, pydantic v2, packaged with hatchling. Declared for the planned engine and app (not
yet imported): numpy, scipy, pandas, lxml, gradio, plotly, mcp, PyYAML, filelock. Optional
extras: `ai` (anthropic, httpx), `parquet` (pyarrow), `xlsx` (openpyxl).

## Architecture

```
            qpilot.schemas  (shared pydantic contracts)
                  ▲      ▲        ▲          ▲
   qpilot.io ─► qpilot.qpcr ─► qpilot.core ─► qpilot.explain / qpilot.ai
   (RDML in)   (domain plugin) (robustness,   (prose from facts only)
                               decisions,
                               store, grades)
                         qpilot.cli  (entry point)
```

`qpilot.core` is domain-agnostic: it talks to the qPCR code only through the `DecisionSpace`
protocol, and a test enforces that importing it does not import `qpilot.qpcr`.

## Getting started

```bash
git clone https://github.com/jeevithg090/qpilot.git
cd qpilot
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
qpilot --version
```

There are no environment variables or secrets to configure. Store tests will use
`QPILOT_STUDIES_DIR` (set automatically by the `tmp_studies_dir` fixture) once the store exists.

## Development

| Task | Command |
|---|---|
| Run the tests | `pytest` |
| Lint | `ruff check .` |
| Format | `ruff format .` (check only: `ruff format --check .`) |
| Type-check | `mypy qpilot tests` |
| Build sdist and wheel | `python -m build` |
| Audit dependencies | `pip-audit` |
| Install git hooks | `pre-commit install` |

Tests marked `demo_data` need the 64-plate dataset at `~/.cache/qpilot/data_vermeulen_raw.rdml`
and skip themselves when it is absent. Unit tests never touch the network.

CI (`.github/workflows/ci.yml`) runs lint, format check and mypy; tests on Python 3.11–3.13;
builds the sdist and wheel and smoke-tests the installed wheel; and audits dependencies.

## Deployment

qPilot is meant to run on the analyst's own computer. Build a wheel with `python -m build` and
install it with `pip install dist/qpilot-*.whl`. It is not published to PyPI.

## Project structure

```
qpilot/
  schemas.py      shared data contracts
  cli/            command-line dispatcher and command registrations
  io/             RDML loading and dataset fetching (planned)
  qpcr/           qPCR domain plugin (planned)
  core/           robustness grid, decisions, store, confidence (planned)
  explain/        explanation templates rendered from facts (planned)
  ai/             optional model layer (planned)
  harness/        model evaluation harness (planned)
  vendor/         vendored third-party code (planned)
tests/
  contracts/      schema and fixture-consistency tests
  fixtures/       contract fixtures and small RDML files (see its README)
  test_cli.py     CLI behaviour
  test_packages.py  package layout and import boundaries
  test_rdml_fixtures.py
```

## Citing and licence

See `CITATION.cff` for how to cite qPilot and the methods it builds on, and
`THIRD_PARTY_NOTICES.md` for third-party code and data. qPilot is licensed under Apache-2.0
(`LICENSE`).
