"""The design-space search (kotatsu/optimize.py): its pieces, without running the FEA."""
from kotatsu import comfort, optimize, params, price

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
