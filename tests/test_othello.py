import pytest

from othello.board import BLACK, WHITE, Board


def test_board_init() -> None:
    board = Board()
    assert BLACK == board.turn
    assert 1 << 28 | 1 << 35 == board.me
    assert 1 << 27 | 1 << 36 == board.opp


@pytest.mark.parametrize(
    ["me", "opp", "turn"],
    (
        [8, 16, BLACK],
        [8, 16, WHITE],
    ),
)
def test_board_from_discs(me: int, opp: int, turn: bool) -> None:
    board = Board.from_discs(me, opp, turn)
    assert me == board.me
    assert opp == board.opp
    assert turn == board.turn


def test_board_from_xot() -> None:
    board = Board.from_xot()
    assert BLACK == board.turn
    assert 12 == board.count(WHITE) + board.count(BLACK)


@pytest.mark.parametrize(
    ["id_str", "expected_board"],
    (
        ["initial", Board()],
        ["xot", None],
        ["B00000000000000010000000000000002", Board.from_discs(1, 2, BLACK)],
        ["W00000000000000010000000000000002", Board.from_discs(2, 1, WHITE)],
        [
            "Bffffffffffffffffffffffffffffffff",
            Board.from_discs(0xFFFFFFFFFFFFFFFF, 0xFFFFFFFFFFFFFFFF, BLACK),
        ],
    ),
)
def test_board_from_id_ok(id_str: str, expected_board: Board) -> None:
    board = Board.from_id(id_str)

    if id_str == "xot":
        assert BLACK == board.turn
        assert 12 == board.count(WHITE) + board.count(BLACK)
        return

    assert expected_board == board


@pytest.mark.parametrize(
    ["id_str", "expected_error_message"],
    (
        ["foo", "unexpected id length"],
        ["123456789012345678901234567890123", "unexpected turn value"],
        ["B0000000X000000000000000000000000", "unexpected base 16 char in discs"],
        ["B00000000000000000000000000X00000", "unexpected base 16 char in discs"],
    ),
)
def test_board_from_id_fail(id_str: str, expected_error_message: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        Board.from_id(id_str)

    assert expected_error_message == exc_info.value.args[0]
