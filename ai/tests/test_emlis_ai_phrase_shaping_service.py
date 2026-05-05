from __future__ import annotations

from emlis_ai_phrase_shaping_service import shape_user_phrases
from emlis_ai_types import EvidenceRef, UserWordAnchor


def test_phrase_shaping_removes_raw_unfinished_connector_and_colloquial_edges():
    evidence = EvidenceRef(kind="emotion", ref_id="emo-cur")
    anchors = [
        UserWordAnchor(anchor_key="a1", text="たまに泣きそうになるくらい嫌になる時あるけどそれだと", role="sadness_surface", evidence=[evidence]),
        UserWordAnchor(anchor_key="a2", text="むかつくけどさ", role="anger_surface", evidence=[evidence]),
        UserWordAnchor(anchor_key="a3", text="教えてくんないんだもん", role="missing_guidance", evidence=[evidence]),
        UserWordAnchor(anchor_key="a4", text="最近めっちゃイライラする", role="anger_surface", evidence=[evidence]),
    ]

    shaped = shape_user_phrases(anchors=anchors, current_input={"id": "emo-cur"})
    phrases = {item.role: item.phrase for item in shaped}

    assert phrases["sadness_surface"] == "泣きそうになるくらい嫌になる時がある"
    assert phrases["anger_surface"] in {"むかつく気持ちもある", "最近かなりイライラが溜まっている"}
    assert any(item.phrase == "教えてもらえないしんどさ" for item in shaped)
    assert any(item.phrase == "最近かなりイライラが溜まっている" for item in shaped)
    assert not any("それだとこと" in item.phrase for item in shaped)
    assert not any("けどこと" in item.phrase for item in shaped)
