"""Manual test: 18 varied payloads across all risk bands and edge cases."""

import json
import urllib.request

BASE_URL = "http://localhost:8000/api/score"


def score(payload, label):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE_URL, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
    band_pad = d["risk_band"].ljust(9)
    print(
        f"  {label}\n"
        f"    score={d['credit_score']}  band={band_pad}  prob={d['repayment_probability']:.3f}"
        f"  cf_actions={len(d['counterfactual_actions'])}\n"
    )


GOOD_SCENARIOS = [
    ("s1_a", "s1_b", 5000, 0),
    ("s2_a", None, 4500, 0),
    ("s3_a", None, 5500, 0),
    ("s4_a", None, 4800, 0),
    ("s5_a", None, 5200, 0),
    ("s6_a", None, 4200, 0),
    ("s8_a", None, 3800, 0),
]
BAD_SCENARIOS = [
    ("s1_c", "s1_a", 350, 5),
    ("s2_c", None, 300, 5),
    ("s3_c", None, 320, 4),
    ("s4_c", None, 310, 5),
    ("s5_c", None, 290, 5),
    ("s6_c", None, 330, 4),
    ("s8_c", None, 300, 5),
]
KEYS = ["s1", "s2", "s3", "s4", "s5", "s6", "s8"]


def make(
    num1=6600,
    num2=1120,
    fin_lit=1,
    crt1=5,
    crt2=47,
    scenarios=None,
    honesty=2,
    text="I budget carefully and repay debts on time. I plan for emergencies and reduce spending when needed.",
    rt_ms=5000,
    acr=0.08,
    dur=420,
    drop=0,
    hes=0.45,
    rsr=0.85,
    tod="afternoon",
    dev="desktop",
    wpm=38.0,
):
    sc = scenarios or GOOD_SCENARIOS
    answers = {
        "numeracy_q1": num1,
        "numeracy_q2": num2,
        "financial_literacy_q1": fin_lit,
        "CRT_q1": crt1,
        "CRT_q2": crt2,
        "honesty_trap_q1": honesty,
        "open_response_text": text,
    }
    for i, key in enumerate(KEYS):
        primary, least, click_ms, changes = sc[i]
        answers[f"scenario_{key}"] = {
            "primary": primary,
            "least": least,
            "first_click_ms": click_ms,
            "change_count": changes,
        }
    return {
        "answers": answers,
        "behavioral": {
            "avg_response_time_ms": rt_ms,
            "answer_change_rate": acr,
            "session_duration_sec": dur,
            "dropout_count": drop,
            "scroll_hesitation_score": hes,
            "risk_response_speed_ratio": rsr,
            "time_of_day": tod,
            "device_type": dev,
            "typing_speed_wpm": wpm,
        },
    }


print("=" * 65)
print("AlterScore Manual Test Suite — 18 payloads")
print("=" * 65)
print()

print("--- EXCELLENT BAND (target 750+) ---")

score(
    make(
        text="I maintain a 6-month emergency fund, track all expenses monthly, always pay early, and invest 15% of income. Financial security is my priority.",
        rt_ms=7000,
        acr=0.03,
        dur=600,
        drop=0,
        hes=0.20,
        rsr=0.95,
        tod="morning",
        dev="desktop",
        wpm=60,
    ),
    "[01] Perfect — ideal cognitive + ideal behavior",
)

score(
    make(
        text="Thirty years of careful budgeting. I lived through 2008, tightened spending, and never missed a payment. Planning is everything.",
        rt_ms=9000,
        acr=0.04,
        dur=750,
        drop=0,
        hes=0.25,
        rsr=0.92,
        tod="morning",
        dev="desktop",
        wpm=22,
    ),
    "[02] Experienced/senior — slow typer, rich deliberate text, careful",
)

print("--- GOOD BAND (target 650-749) ---")

score(
    make(
        scenarios=[
            ("s1_a", "s1_b", 4200, 1),
            ("s2_a", None, 3800, 1),
            ("s3_a", None, 4500, 0),
            ("s4_a", None, 4100, 1),
            ("s5_a", None, 4800, 0),
            ("s6_a", None, 3700, 1),
            ("s8_a", None, 3300, 0),
        ],
        text="I have a budget and try to save. Sometimes unexpected costs come up but I manage by cutting back.",
        rt_ms=4800,
        acr=0.15,
        dur=380,
        drop=0,
        hes=0.45,
        rsr=0.80,
        wpm=42,
    ),
    "[03] Solid good — mostly correct, normal behavior",
)

score(
    make(
        text="I save a portion of my income monthly and avoid high-interest debt. I try to repay obligations ahead of schedule when possible.",
        rt_ms=5500,
        acr=0.08,
        dur=460,
        drop=0,
        hes=0.38,
        rsr=0.88,
        wpm=44,
        crt1=5,
        crt2=47,
        num1=6600,
        num2=1120,
    ),
    "[04] Good cognitive + positive text + deliberate",
)

score(
    make(
        text="I maintain a budget. I save some money each month and try to avoid unnecessary purchases.",
        rt_ms=5500,
        acr=0.10,
        dur=460,
        drop=0,
        hes=0.42,
        rsr=0.85,
        tod="morning",
        dev="desktop",
        wpm=35,
        crt1=5,
        crt2=47,
        num1=6600,
        num2=1120,
    ),
    "[05] Solid good — clean behavior, good cognition",
)

print("--- FAIR BAND (target 550-649) ---")

score(
    make(
        num1=5000,
        num2=900,
        fin_lit=1,
        crt1=5,
        crt2=30,
        text="I try to save a bit each month and avoid unnecessary debt.",
        rt_ms=5500,
        acr=0.10,
        dur=450,
        drop=0,
        hes=0.50,
        rsr=0.80,
        wpm=35,
    ),
    "[06] Average cognitive + deliberate behavior",
)

score(
    make(
        rt_ms=5000,
        acr=0.12,
        dur=350,
        drop=2,
        hes=0.55,
        rsr=0.75,
        wpm=32,
        num1=5500,
        num2=1000,
        fin_lit=1,
        crt1=5,
        crt2=35,
    ),
    "[07] Moderate + 2 dropouts mid-session",
)

score(
    make(
        rt_ms=4500,
        acr=0.12,
        dur=380,
        drop=1,
        hes=0.60,
        rsr=0.70,
        tod="night",
        dev="mobile",
        wpm=28,
    ),
    "[08] Good cognitive + night/mobile + one dropout",
)

score(
    make(
        text="ok",
        rt_ms=3500,
        acr=0.15,
        dur=320,
        drop=1,
        hes=0.60,
        rsr=0.70,
        wpm=15,
    ),
    "[09] Minimal open-text response",
)

print("--- POOR BAND (target 300-549) ---")

score(
    make(
        num1=2000,
        num2=400,
        fin_lit=0,
        crt1=10,
        crt2=20,
        scenarios=BAD_SCENARIOS,
        text="idk",
        rt_ms=320,
        acr=0.85,
        dur=45,
        drop=3,
        hes=0.90,
        rsr=0.10,
        tod="night",
        dev="mobile",
        wpm=5,
    ),
    "[10] Weak cognitive + fast clicks + gaming behavior",
)

score(
    make(
        scenarios=[
            ("s1_a", "s1_b", 500, 0),
            ("s2_a", None, 480, 0),
            ("s3_a", None, 510, 0),
            ("s4_a", None, 495, 0),
            ("s5_a", None, 505, 0),
            ("s6_a", None, 490, 0),
            ("s8_a", None, 500, 0),
        ],
        text="I always pay on time.",
        rt_ms=490,
        acr=0.00,
        dur=55,
        drop=0,
        hes=0.92,
        rsr=0.05,
        wpm=3,
    ),
    "[11] Straight-liner — same answer, ultra-fast, no changes",
)

score(
    make(
        scenarios=[
            ("s1_a", "s1_b", 200, 0),
            ("s2_a", None, 180, 0),
            ("s3_a", None, 210, 0),
            ("s4_a", None, 190, 0),
            ("s5_a", None, 220, 0),
            ("s6_a", None, 200, 0),
            ("s8_a", None, 195, 0),
        ],
        text="yes",
        rt_ms=200,
        acr=0.00,
        dur=25,
        drop=0,
        hes=0.98,
        rsr=0.02,
        wpm=2,
    ),
    "[12] Bot-like — sub-200ms, 25s session, trivial text",
)

score(
    make(
        honesty=5,
        text="I always pay everything perfectly on time and have never ever missed any payment in my entire life.",
        rt_ms=5000,
        acr=0.10,
        dur=400,
        drop=0,
        hes=0.45,
        rsr=0.80,
        wpm=40,
    ),
    "[13] Honesty trap triggered (score=5 = max dishonesty)",
)

score(
    make(
        text="I am extremely financially responsible and always save and invest perfectly and have zero debt.",
        scenarios=BAD_SCENARIOS,
        rt_ms=290,
        acr=0.90,
        dur=35,
        drop=2,
        hes=0.95,
        rsr=0.05,
        wpm=4,
        honesty=4,
    ),
    "[14] Contradictory — perfect text vs terrible behavior/gaming",
)

score(
    make(
        num1=0,
        num2=0,
        fin_lit=0,
        crt1=100,
        crt2=1,
        scenarios=[
            ("s1_c", "s1_a", 150, 5),
            ("s2_c", None, 140, 5),
            ("s3_c", None, 160, 5),
            ("s4_c", None, 145, 5),
            ("s5_c", None, 155, 5),
            ("s6_c", None, 148, 5),
            ("s8_c", None, 152, 5),
        ],
        honesty=5,
        text="x",
        rt_ms=150,
        acr=0.99,
        dur=20,
        drop=5,
        hes=0.99,
        rsr=0.01,
        tod="night",
        dev="mobile",
        wpm=1,
    ),
    "[15] Absolute worst — every signal maximally bad",
)

print("--- EDGE CASES ---")

score(
    make(
        num1=1000,
        num2=200,
        fin_lit=0,
        crt1=0,
        crt2=5,
        text="I focus on doing the right thing in practice even if I struggle with calculations.",
        rt_ms=5500,
        acr=0.06,
        dur=460,
        drop=0,
        hes=0.38,
        rsr=0.88,
        wpm=44,
    ),
    "[16] Wrong numeracy/CRT + perfect scenario behavior",
)

score(
    make(
        crt1=10,
        crt2=48,
        text="I save every month and always pay debts early. Financial planning is a top priority for me.",
        rt_ms=5500,
        acr=0.06,
        dur=480,
        drop=0,
        hes=0.35,
        rsr=0.88,
        wpm=45,
    ),
    "[17] Perfect behavior + wrong CRT only",
)

score(
    make(
        scenarios=[
            ("s1_a", "s1_b", 6000, 5),
            ("s2_a", None, 5800, 5),
            ("s3_a", None, 6200, 4),
            ("s4_a", None, 5900, 5),
            ("s5_a", None, 6100, 5),
            ("s6_a", None, 5700, 4),
            ("s8_a", None, 5500, 5),
        ],
        rt_ms=6000,
        acr=0.70,
        dur=720,
        drop=1,
        hes=0.60,
        rsr=0.70,
        wpm=28,
    ),
    "[18] Highly indecisive — many changes, long slow session",
)

print("=" * 65)
print("Done.")
