"""The design-space search (kotatsu/optimize.py): its pieces, without running the FEA."""
from kotatsu import comfort, looks, optimize, params, price

P = params.tables(params.load())[0]


def test_knobs_cover_the_current_design():
    rng, cur = optimize.knob_ranges(P), optimize.current_knobs(P)
    assert rng and set(rng) == set(cur)
    for k, (lo, hi) in rng.items():
        assert lo < hi and lo <= cur[k] <= hi, k


def test_design_applies_knobs_to_fresh_params():
    p = optimize.design({"yagura.leg_narrow": 81.0})
    assert p.yagura.leg_narrow == 81.0
    assert optimize.design({}).yagura.leg_narrow == P.yagura.leg_narrow     # nothing leaks between designs


def test_sample_is_deterministic_and_in_range():
    a, b = optimize.sample(P, 12, 3), optimize.sample(P, 12, 3)
    assert a == b and len(a) == 12
    for s in a:
        for k, (lo, hi) in optimize.knob_ranges(P).items():
            assert lo - 0.05 <= s[k] <= hi + 0.05


def test_cheap_checks_on_the_current_design():
    r = optimize.cheap(optimize.current_knobs(P))
    assert r["ok"], r.get("why")
    assert r["price"] == price.estimate(P)["subtotal"]
    assert r["room"] == round(comfort.legroom(P), 1) and r["neg_room"] == -r["room"]
    assert r["kg"] <= P.shipping.free_kg
    assert r["look"] == round(looks.leg_width(P), 2) and r["room"] >= P.comfort.legroom_min


def test_cheap_rejects_a_foot_wider_than_the_leg():
    k = optimize.current_knobs(P)
    k["yagura.leg_foot_w"] = k["yagura.leg_narrow"] + 5
    assert not optimize.cheap(k)["ok"]


def test_legroom_narrows_with_wider_legs():
    assert comfort.legroom(optimize.design({"yagura.leg_narrow": 85.0})) < comfort.legroom(P)


def test_nondominated_and_fronts():
    rows = [{"a": 1, "b": 3}, {"a": 2, "b": 2}, {"a": 3, "b": 1}, {"a": 3, "b": 3}, {"a": 2, "b": 2}]
    assert optimize.nondominated(rows, ("a", "b")) == [0, 1, 2, 4]      # ties both stay
    assert optimize.fronts(rows, ("a", "b")) == [[0, 1, 2, 4], [3]]


def test_leg_width_tracks_the_legs():
    w = looks.leg_width(P)
    assert 50 < w < 90
    assert looks.leg_width(optimize.design({"yagura.leg_narrow": 85.0})) > w > looks.leg_width(optimize.design({"yagura.leg_narrow": 62.0}))


def test_picks_spread_and_score():
    cur = {"price": 100.0, "look": 60.0}
    rows = [{"price": 99.0, "look": 66.0}, {"price": 101.0, "look": 57.0}, {"price": 100.5, "look": 59.0}]
    p = optimize.picks(rows, cur)
    assert p["slimmest"] is rows[1] and p["cheapest"] is rows[0]
    assert p["balanced (1 % cheaper = 1 % slimmer)"] is rows[1]          # -5 % width beats -1 % price
    s = optimize.spread([{"look": float(i), "price": 1.0} for i in range(10)], 4)
    assert [r["look"] for r in s] == [0.0, 3.0, 6.0, 9.0]


def test_mutate_stays_in_range():
    import numpy as np
    for m in optimize.mutate(P, optimize.current_knobs(P), 20, 0.5, np.random.default_rng(1)):
        for k, (lo, hi) in optimize.knob_ranges(P).items():
            assert lo <= m[k] <= hi


def test_heavy_runs_the_cases_that_exist(monkeypatch):
    """Stage 2's plumbing, with the FEA stubbed out: it only asks for cases fea.py has (one plate a corner: a
    stage 2 that still asked for the "+" legs' plate B crashed every run), and takes the worst of them."""
    from kotatsu import fea
    calls = []

    def leg_case(p, which, H, top=None, **kw):
        calls.append((which, top is not None))
        if which != "A":
            raise ValueError(which)
        return {"sway_mm": 2.0, "zones": {"slot root": {"tsai_hill": 0.7 if top else 0.6},
                                          "contact edges": {"tsai_hill": 9.0}}}

    monkeypatch.setattr(fea, "leg_case", leg_case)
    monkeypatch.setattr(fea, "deck_case", lambda p, ld, **kw: {k: {"tsai_hill": 0.5} for k in ("fillets", "arms", "ring", "pads")})
    monkeypatch.setattr(optimize, "_TOP", {"A post": 100.0, "A tenon": 50.0})
    r = optimize.heavy(optimize.current_knobs(P))
    assert sorted(calls) == [("A", False), ("A", True)]
    assert r["sway"] == 2.0 and r["use"] == 0.7, "contact edges (local bearing) stay out of the worst"
    assert set(r["use_by_part"]) == {"leg", "leg + top load", "deck"}
