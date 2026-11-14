"""The pydantic contracts accept valid data and reject what the layers must never exchange."""

import pytest
from pydantic import ValidationError

from qpilot.schemas import (
    CardOption,
    Check,
    ContrastResult,
    DecisionCard,
    DecisionEntry,
    Fact,
    Grade,
)

CONTRAST = {
    "target": "ODC1",
    "log2fc": 1.84,
    "fc": 3.58,
    "ci": [2.6, 4.9],
    "p": 1e-6,
    "t": 6.1,
    "n_hi": 53,
    "n_lo": 294,
    "conclusion": "up",
}


def test_contrast_result_coerces_ci_to_tuple():
    result = ContrastResult.model_validate(CONTRAST)
    assert result.ci == (2.6, 4.9)


@pytest.mark.parametrize("conclusion", ["UP", "increase", "", None])
def test_contrast_result_rejects_unknown_conclusion(conclusion):
    with pytest.raises(ValidationError):
        ContrastResult.model_validate({**CONTRAST, "conclusion": conclusion})


def test_contrast_result_rejects_malformed_ci():
    with pytest.raises(ValidationError):
        ContrastResult.model_validate({**CONTRAST, "ci": [1.0, 2.0, 3.0]})


def test_grade_is_ordinal_never_a_probability():
    with pytest.raises(ValidationError):
        Grade(level=0.8, reasons=[], checks=[])
    grade = Grade(level="Low", reasons=["imprecise"], checks=[Check(id="x", passed=False, note="")])
    assert grade.min_flip_changes is None


def test_mutable_defaults_are_not_shared():
    first, second = Check(id="a", passed=True, note=""), Check(id="b", passed=True, note="")
    first.fact_ids.append("f_1")
    assert second.fact_ids == []


def test_fact_values_keep_their_type():
    assert Fact(id="f_n", value=64).value == 64
    assert isinstance(Fact(id="f_x", value=1.5).value, float)
    assert Fact(id="f_s", value="HPRT1").value == "HPRT1"


def test_decision_card_defaults_to_an_open_suggestion():
    card = DecisionCard(
        id="card_x",
        kind="group_cutoff",
        rank=1,
        impact={},
        evidence={},
        options=[CardOption(id="a", label="A", per_gene={})],
        recommended="a",
        rationale_template="",
        facts=[],
    )
    assert (card.status, card.autonomy, card.effective_autonomy) == ("open", "suggest", "suggest")
    assert card.decision is None and card.decided_by is None


def test_decision_card_rejects_unknown_kind():
    with pytest.raises(ValidationError):
        DecisionCard.model_validate(
            {
                "id": "c",
                "kind": "colour_scheme",
                "rank": 1,
                "impact": {},
                "evidence": {},
                "options": [],
                "recommended": "a",
                "rationale_template": "",
                "facts": [],
            }
        )


def test_decision_entry_rejects_unknown_actor():
    with pytest.raises(ValidationError):
        DecisionEntry(
            seq=0,
            prev_hash="0" * 64,
            card_id="c",
            option="a",
            reason="",
            actor="robot",
            status="applied",
            at="2026-10-17T00:00:00Z",
        )
