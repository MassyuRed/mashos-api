"""Public synthetic contact-boundary regressions; no real user material."""
import pytest
from piece_v2_contract import PieceContractError
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate


@pytest.mark.parametrize('contact', [
    'sample@example.test', 'Sample@EXAMPLE.TEST', 'name+tag@example.test',
])
def test_email_adjacent_to_japanese_is_not_emitted(contact):
    text = f'私が大切にしたいのは、連絡先を{contact}にしておくことです。'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-source', '1', text)
    with pytest.raises(PieceContractError):
        generate_piece_candidate(source, authenticated_owner_id='synthetic-owner')
