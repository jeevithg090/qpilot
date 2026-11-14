# Test fixtures

| File | What it is | Source / licence |
|---|---|---|
| `results.json`, `cards.json`, `facts.json` | Contract fixtures (`qpilot.schemas.StudyResult`, `list[DecisionCard]`, `dict[str, Fact]`) for the 64-plate Vermeulen demo study. Every layer is built against them until the engine can regenerate them; `tests/contracts/test_fixtures.py` checks they are internally consistent. | Generated from rdmlpython @ `fce7a44` LinRegPCR output on `data_vermeulen_raw.rdml` with an offline verification script (not in this repository). |
| `test_mca_1_raw_data.rdml` | Small real RDML file (32 KB) for unit tests that must run without the demo dataset. | rdmlpython repository @ `fce7a44`, `test/`, MIT. |
| `xxe.rdml` | Three-line RDML with an external entity declaration (`canary.txt`), used to prove the loader never resolves external entities. | Written for qPilot. |

Do not add the demo dataset here; it is fetched at runtime and never committed.
