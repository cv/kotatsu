"""The 3-D tab's assembly animation (kotatsu/assembly.py): every part has a path home, the steps follow
the real order, and each part starts clear of what it goes into."""
import pytest

from kotatsu import assembly, frame, params, site, yagura

P = params.tables(params.load())[0]
L = frame.layout(P)
FD = site.frame_data(P)
EXTRAS = FD["assembly"]


def first_from(name, kind=None):
    return [pl["moves"] for pl in FD["placed"] if pl["part"] == name and (kind is None or pl["kind"] == kind)]


def test_every_part_has_a_valid_path():
    n = len(EXTRAS["steps"])
    for pl in FD["placed"]:
        assert pl["moves"], pl["part"]
        for m in pl["moves"]:
            assert 0 <= m["step"] < n and 0 <= m["a"] < m["b"] <= 1, (pl["part"], m)


def test_every_step_moves_something():
    used = {m["step"] for pl in FD["placed"] for m in pl["moves"]}
    used |= {m["step"] for k in ("heater", "futon", "top", "tea") for m in EXTRAS[k]}
    assert used == set(range(len(EXTRAS["steps"])))


def test_steps_follow_the_real_order():
    S = EXTRAS["steps"]
    order = [assembly.LEGS, assembly.STAND, assembly.DECK, assembly.LEG_WEDGES, assembly.CRADLE,
             assembly.LOWER, assembly.FUTON, assembly.TOP]
    assert order == sorted(order) and "deck" in S[assembly.DECK] and "heater" in S[assembly.CRADLE].lower()


def test_parts_start_clear():
    deck = first_from("deck")[0][0]["from"]
    assert L.z_deck_bot + deck[2] > L.H, "the deck starts above the tenon tops"
    for moves in first_from("leg crosspiece" if yagura.diagonal(P) else "leg plate B"):
        assert moves[0]["step"] == assembly.LEGS and moves[0]["from"][2] >= yagura.lap_depth(P)
    lift = assembly.cradle_lift(P)
    for moves in first_from("heater cheek"):                  # put together above the table, then lowered in
        assert [m["step"] for m in moves] == [assembly.CRADLE, assembly.LOWER]
        assert moves[1]["from"][2] == lift and frame.cheek_z(P)[0] + lift > L.H, "starts above the post tops"
    (_, _, sz), (_, _, hz) = frame.heater_box(P)
    assert [m["step"] for m in EXTRAS["heater"]] == [assembly.CRADLE, assembly.LOWER]
    assert EXTRAS["heater"][1]["from"][2] == lift, "the heater travels with its cheeks"


@pytest.mark.parametrize("pl", [pl for pl in FD["placed"] if pl["kind"] == "wedge"], ids=lambda pl: str(pl["origin"]))
def test_wedges_slide_in_tip_first_along_their_length(pl):
    (m,) = pl["moves"]
    fx, fy, fz = m["from"]
    if pl["axis"] == "m":                           # matrix-placed: its own u (length) and w (thickness) axes
        M = pl["matrix"]
        along, across = fx * M[0] + fy * M[4], fx * M[2] + fy * M[6]
        across = round(across, 6)
    else:
        along = fx if pl["axis"] == "x" else fy
        across = fy if pl["axis"] == "x" else fx
    assert along > 0 and across == 0 and fz == 0     # tip at u = 0 leads, so it starts toward the head (+u)
