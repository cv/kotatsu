"""The zaisu by finite elements (kotatsu/fea_chair.py, docs/fea.md): forces balance, and every part holds
its check load on the thinnest stock, grain the weaker way round."""
import pytest

from kotatsu import fea_chair, params, zaisu

P = params.tables(params.load())[0]
Z = P.zaisu


@pytest.fixture(scope="module")
def seat():
    return fea_chair.seat_case(P)


@pytest.fixture(scope="module")
def back():
    return fea_chair.back_case(P)


@pytest.fixture(scope="module")
def side():
    return fea_chair.side_case(P, Z.back_check_n, Z.sitter_n)


def test_forces_balance(seat, back, side):
    w = zaisu.board(P).area * P.material.density_kg_m3 * 1e-9 * P.material.t_min * 9.81
    assert seat["support_N"] == pytest.approx(Z.seat_check_n + w, rel=1e-3)
    assert back["support_N"] == pytest.approx(Z.back_check_n, rel=1e-3)
    assert side["forces"]["floor"] == pytest.approx(Z.sitter_n / 2, abs=1.0)            # each side: half the sitter
    assert side["forces"]["floor (grip)"] == pytest.approx(-Z.back_check_n / 2, abs=1.0)  # ... and half the lean


def test_parts_hold(seat, back, side):
    for r in (seat, back, side):
        assert r["peak"]["tsai_hill"] < 0.8, r["part"]
    assert side["peak"]["tsai_hill"] < 0.75          # the corner behind the post (85 % before its fillet grew)


def test_plates_stay_clear(seat, back):
    assert seat["sag_mm"] < Z.board_lift - 5          # the seat stays off the floor
    assert back["sag_mm"] < 10.0
