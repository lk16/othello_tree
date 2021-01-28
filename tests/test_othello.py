import pytest

from othello.bits import bits_rotate
from othello.board import BLACK, EMPTY, MOVE_PASS, VALID_MOVE, WHITE, Board


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


@pytest.mark.parametrize(
    ["board", "expected_black", "expected_white"],
    (
        [Board.from_discs(1, 2, BLACK), 1, 2],
        [Board.from_discs(1, 2, WHITE), 2, 1],
    ),
)
def test_board_black(board: Board, expected_black: int, expected_white: int) -> None:
    assert expected_black == board.black()
    assert expected_white == board.white()


def test_board_image_file_name() -> None:
    assert "jpg/00000008100000000000001008000000.jpg" == Board().get_image_file_name()


def test_get_fields() -> None:
    expected = [EMPTY] * 64
    expected[28] = expected[35] = BLACK
    expected[27] = expected[36] = WHITE
    expected[19] = expected[26] = expected[37] = expected[44] = VALID_MOVE
    assert expected == Board().get_fields()


def test_board_to_id() -> None:
    assert "B00000008100000000000001008000000" == Board().to_id()


def test_board_field_index_conversion() -> None:

    pairs = [(MOVE_PASS, "--")]

    for x, col in enumerate("abcdefgh"):
        for y, row in enumerate("12345678"):
            index = 8 * y + x
            field = f"{col}{row}"
            pairs.append((index, field))

    for index, field in pairs:
        assert index == Board.field_to_index(field)
        assert index == Board.field_to_index(field.upper())
        assert field == Board.index_to_field(index)


@pytest.mark.parametrize(
    ["expected", "rotation"],
    (
        [0x22120A0E1222221E, 0],
        [0x4448507048444478, 1],
        [0x1E2222120E0A1222, 2],
        [0x7844444870504844, 3],
        [0x000086493111FF00, 4],
        [0x00FF113149860000, 5],
        [0x000061928C88FF00, 6],
        [0x00FF888C92610000, 7],
    ),
)
def test_bits_rotate(expected: int, rotation: int) -> None:
    assert expected == bits_rotate(0x22120A0E1222221E, rotation)


@pytest.mark.parametrize(
    ["bits", "rotation"],
    (
        [0x22120A0E1222221E, 6],
        [0x4448507048444478, 7],
        [0x1E2222120E0A1222, 4],
        [0x7844444870504844, 5],
        [0x000086493111FF00, 1],
        [0x00FF113149860000, 3],
        [0x000061928C88FF00, 0],
        [0x00FF888C92610000, 2],
    ),
)
@pytest.mark.parametrize("turn", [WHITE, BLACK])
def test_board_normalized(bits: int, rotation: int, turn: int) -> None:
    board = Board.from_discs(bits, 0, turn)

    assert (
        Board.from_discs(0x000061928C88FF00, 0, turn),
        rotation,
    ) == board.normalized()

    board = Board.from_discs(0, bits, turn)

    assert (
        Board.from_discs(0, 0x000061928C88FF00, turn),
        rotation,
    ) == board.normalized()


@pytest.mark.parametrize(
    ["bits"],
    (
        [0x22120A0E1222221E],
        [0x4448507048444478],
        [0x1E2222120E0A1222],
        [0x7844444870504844],
        [0x000086493111FF00],
        [0x00FF113149860000],
        [0x000061928C88FF00],
        [0x00FF888C92610000],
    ),
)
@pytest.mark.parametrize("turn", [WHITE, BLACK])
def test_board_denormalized(bits: int, turn: int) -> None:
    board = Board.from_discs(bits, 0, turn)
    normalized, rotation = board.normalized()
    assert board == normalized.denormalized(rotation)

    board = Board.from_discs(0, bits, turn)
    normalized, rotation = board.normalized()
    assert board == normalized.denormalized(rotation)
