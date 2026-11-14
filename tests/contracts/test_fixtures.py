"""The contract fixtures are valid and internally consistent.

The fixtures describe the 64-plate Vermeulen demo study. Every layer is built and tested against
them, so a fixture that contradicts itself would hide bugs everywhere downstream.
"""

import math
import re
import statistics
from typing import Any

import pytest

from qpilot.schemas import ContrastResult, DecisionCard, StudyResult

# Fact paths that describe where a number came from but have no field in StudyResult.
# ``cards.card_refset.worst`` is checked separately in test_worst_reference_fact.
UNSTRUCTURED_PATH = re.compile(r"^study$|^confidence\.[^.]+\.mde$|^cards\.card_refset\.worst$")
PATH_PART = re.compile(r"\[(-?\d+)\]|([^.\[\]]+)")


def conclude(result: ContrastResult, rule: dict[str, float]) -> str:
    """The conclusion rule stated in ``StudyResult.conclusion_rule``."""
    if result.p >= rule["alpha"] or abs(result.log2fc) < rule["min_log2fc"]:
        return "none"
    return "up" if result.log2fc > 0 else "down"


def resolve(path: str, root: dict[str, Any]) -> Any:
    """Follow a fact path such as ``contrasts.ODC1.ci[1]`` or ``genorm.order[-1]``."""
    node: Any = root
    for index, key in PATH_PART.findall(path):
        node = node[int(index)] if index else node[key]
    return node


@pytest.fixture
def fact_root(fixture_result: StudyResult, fixture_cards: list[DecisionCard]) -> dict[str, Any]:
    root = fixture_result.model_dump()
    root["cards"] = {
        option.id: {gene: c.model_dump() for gene, c in option.per_gene.items()}
        for card in fixture_cards
        for option in card.options
    }
    return root


def test_locked_study_numbers(fixture_result):
    r = fixture_result
    assert (r.n_plates, r.n_reactions, r.n_samples) == (64, 24576, 366)
    assert (r.design.n_hi, r.design.n_lo) == (53, 294)
    assert r.genorm.order == ["ALUsq(Eurogentec)", "HPRT1", "HMBS", "SDHA(1)", "UBC(2)"]
    odc1 = r.contrasts["ODC1"]
    assert odc1.fc == pytest.approx(3.59, abs=0.1) and odc1.conclusion == "up"
    assert r.robustness["ODC1"].holds == 1.0
    assert r.robustness["NM23A"].holds == pytest.approx(0.645, abs=0.02)
    assert r.confidence["ODC1"].level == "Moderate"
    assert len(r.confidence["ODC1"].reasons) == 1
    assert r.confidence["NM23A"].level == "Very low"


def test_results_round_trip_through_json(fixture_result):
    again = StudyResult.model_validate_json(fixture_result.model_dump_json())
    assert again == fixture_result


def test_every_gene_has_contrast_robustness_and_grade(fixture_result):
    genes = set(fixture_result.contrasts)
    assert genes == set(fixture_result.robustness) == set(fixture_result.confidence)
    assert all(fixture_result.contrasts[g].target == g for g in genes)


def test_contrasts_are_arithmetically_consistent(fixture_result):
    for gene, c in fixture_result.contrasts.items():
        assert c.fc == pytest.approx(2**c.log2fc, rel=1e-3), gene
        assert c.ci[0] <= c.fc <= c.ci[1], gene
        assert 0.0 <= c.p <= 1.0, gene
        assert c.n_hi <= fixture_result.design.n_hi and c.n_lo <= fixture_result.design.n_lo


def test_conclusions_follow_the_stated_rule(fixture_result, fixture_cards):
    rule = fixture_result.conclusion_rule
    for c in fixture_result.contrasts.values():
        assert c.conclusion == conclude(c, rule), c.target
    for card in fixture_cards:
        for option in card.options:
            for c in option.per_gene.values():
                assert c.conclusion == conclude(c, rule), (card.id, option.id, c.target)


def test_robustness_agrees_with_primary_analysis(fixture_result):
    for gene, rob in fixture_result.robustness.items():
        primary = fixture_result.contrasts[gene]
        assert rob.conclusion == primary.conclusion, gene
        assert math.isclose(rob.fc, primary.fc, rel_tol=1e-6), gene
        assert 0.0 <= rob.holds <= 1.0 and rob.n_cells > 0, gene


def test_genorm_recommendation_is_drawn_from_the_ranking(fixture_result):
    g = fixture_result.genorm
    assert set(g.recommended) <= set(g.order) == set(g.M_initial)
    assert set(fixture_result.design.refs_primary) == set(g.recommended)


def test_cards_are_ranked_and_recommend_one_of_their_options(fixture_cards):
    assert [c.id for c in fixture_cards] == ["card_refset", "card_cutoff", "card_undetermined"]
    assert [c.rank for c in fixture_cards] == [1, 2, 3]
    assert [c.impact["n_genes_flipped"] for c in fixture_cards] == [31, 17, 0]
    assert fixture_cards[2].status == "auto_decided"
    for card in fixture_cards:
        option_ids = [o.id for o in card.options]
        assert len(option_ids) == len(set(option_ids)), card.id
        assert card.recommended in option_ids, card.id
        assert card.impact["flips"] == (card.impact["n_genes_flipped"] > 0), card.id


def test_recommended_option_reproduces_the_primary_contrasts(fixture_result, fixture_cards):
    for card in fixture_cards:
        option = next(o for o in card.options if o.id == card.recommended)
        for gene, c in option.per_gene.items():
            assert c.fc == pytest.approx(fixture_result.contrasts[gene].fc), (card.id, gene)


def test_fact_ids_are_consistent(fixture_result, fixture_cards, fixture_facts):
    assert fixture_result.facts == fixture_facts
    assert all(fid == fact.id for fid, fact in fixture_facts.items())
    referenced = {fid for card in fixture_cards for fid in card.facts}
    referenced |= {
        fid
        for grade in fixture_result.confidence.values()
        for ch in grade.checks
        for fid in ch.fact_ids
    }
    missing = sorted(referenced - set(fixture_facts))
    assert not missing, f"unknown fact ids: {missing[:5]}"


def test_fact_formats_render(fixture_facts):
    for fact in fixture_facts.values():
        assert fact.fmt.format(fact.value), fact.id


def test_fact_values_match_the_results_they_point_to(fixture_facts, fact_root):
    checked = 0
    for fact in fixture_facts.values():
        if UNSTRUCTURED_PATH.match(fact.path):
            continue
        actual = resolve(fact.path, fact_root)
        if isinstance(actual, dict):  # an aggregate fact, e.g. the median efficiency
            actual = statistics.median(actual.values())
        if isinstance(fact.value, float):
            assert actual == pytest.approx(fact.value, rel=1e-5), fact.id
        else:
            assert actual == fact.value, fact.id
        checked += 1
    assert checked > 400  # guard against the path filter silently skipping everything


def test_worst_reference_fact(fixture_cards, fixture_facts):
    worst_ref = fixture_facts["f_worst_ref"].value
    assert isinstance(worst_ref, str)
    option_id = re.sub(r"\W+", "_", worst_ref.lower()).strip("_") + "_alone"
    refset = next(c for c in fixture_cards if c.id == "card_refset")
    option = next(o for o in refset.options if o.id == option_id)
    assert option.per_gene["ODC1"].fc == pytest.approx(fixture_facts["f_fc_odc1_worst"].value)


def test_resolve_handles_indices_and_special_keys():
    root = {"genorm": {"order": ["A", "B"], "V": {"V2/3": 0.5}, "M": {"SDHA(1)": 1.9}}}
    assert resolve("genorm.order[-1]", root) == "B"
    assert resolve("genorm.V.V2/3", root) == 0.5
    assert resolve("genorm.M.SDHA(1)", root) == 1.9
