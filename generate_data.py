"""Generate a SYNTHETIC clinical trial dataset (DM, AE, LB) with deliberately injected errors.
All data is fake. Errors are injected so the validation scripts have something to find."""
import numpy as np
import pandas as pd
from datetime import date, timedelta

rng = np.random.default_rng(42)
STUDY = "STUDY01"
N = 60
SITES = [101, 102, 103, 104, 105]
iso = lambda d: d.isoformat()

# ---------- DM (Demographics) ----------
rows = []
for i in range(1, N + 1):
    site = int(rng.choice(SITES))
    consent = date(2025, 1, 1) + timedelta(days=int(rng.integers(0, 120)))
    first_dose = consent + timedelta(days=int(rng.integers(3, 15)))
    rows.append({
        "USUBJID": f"{STUDY}-{site}-{i:03d}", "SITEID": site,
        "AGE": int(rng.integers(18, 76)), "SEX": rng.choice(["M", "F"]),
        "ARM": rng.choice(["PLACEBO", "DRUG 10MG"]),
        "RFICDTC": iso(consent), "RFSTDTC": iso(first_dose),
    })
dm = pd.DataFrame(rows)

# ---------- AE (Adverse Events) ----------
terms = ["HEADACHE", "NAUSEA", "FATIGUE", "DIZZINESS", "RASH", "VOMITING", "COUGH", "INSOMNIA"]
ae_rows = []
for _, s in dm.iterrows():
    if rng.random() < 0.7:
        for _ in range(int(rng.integers(1, 4))):
            start = date.fromisoformat(s.RFSTDTC) + timedelta(days=int(rng.integers(1, 60)))
            end = start + timedelta(days=int(rng.integers(1, 15)))
            ae_rows.append({
                "USUBJID": s.USUBJID, "AETERM": rng.choice(terms),
                "AESTDTC": iso(start), "AEENDTC": iso(end),
                "AESEV": rng.choice(["MILD", "MODERATE", "SEVERE"], p=[0.6, 0.3, 0.1]),
                "AESER": rng.choice(["N", "Y"], p=[0.93, 0.07]),
            })
ae = pd.DataFrame(ae_rows)

# ---------- LB (Labs) ----------
tests = {  # code: (unit, low, high, mean, sd)
    "ALT": ("U/L", 7, 56, 25, 8), "AST": ("U/L", 10, 40, 24, 6),
    "CREAT": ("mg/dL", 0.6, 1.3, 0.9, 0.15), "HGB": ("g/dL", 12, 17, 14, 1.2),
}
visits = {"SCREENING": 0, "WEEK 4": 28, "WEEK 8": 56}
lb_rows = []
for _, s in dm.iterrows():
    for visit, offset in visits.items():
        d = date.fromisoformat(s.RFICDTC) + timedelta(days=offset + int(rng.integers(0, 3)))
        for code, (unit, lo, hi, mu, sd) in tests.items():
            lb_rows.append({
                "USUBJID": s.USUBJID, "VISIT": visit, "LBTESTCD": code,
                "LBORRES": round(float(rng.normal(mu, sd)), 1), "LBORRESU": unit,
                "LBSTNRLO": lo, "LBSTNRHI": hi, "LBDTC": iso(d),
            })
lb = pd.DataFrame(lb_rows)

# ---------- Inject errors ----------
# 1) AE starts before informed consent
for idx in rng.choice(ae.index, 3, replace=False):
    c = dm.loc[dm.USUBJID == ae.at[idx, "USUBJID"], "RFICDTC"].iloc[0]
    ae.at[idx, "AESTDTC"] = iso(date.fromisoformat(c) - timedelta(days=5))
# 2) AE end before start
for idx in rng.choice(ae.index, 3, replace=False):
    ae.at[idx, "AEENDTC"] = iso(date.fromisoformat(ae.at[idx, "AESTDTC"]) - timedelta(days=2))
# 3) Missing severity
ae.loc[rng.choice(ae.index, 4, replace=False), "AESEV"] = np.nan
# 4) Duplicate AE records
ae = pd.concat([ae, ae.sample(2, random_state=1)], ignore_index=True)
# 5) Orphan AE (subject not in DM)
ae = pd.concat([ae, pd.DataFrame([{"USUBJID": f"{STUDY}-999-999", "AETERM": "HEADACHE",
    "AESTDTC": "2025-03-01", "AEENDTC": "2025-03-04", "AESEV": "MILD", "AESER": "N"}])], ignore_index=True)
# 6) Implausible ages
dm.loc[rng.choice(dm.index, 2, replace=False), "AGE"] = [17, 150]
# 7) Impossible lab values (HGB typed wrongly) and missing results
hgb = lb[lb.LBTESTCD == "HGB"].index
lb.loc[rng.choice(hgb, 3, replace=False), "LBORRES"] = [1.4, 140.0, 0.5]
lb.loc[rng.choice(lb.index, 5, replace=False), "LBORRES"] = np.nan
# 8) Lab drawn before consent
scr = lb[lb.VISIT == "SCREENING"].index
for idx in rng.choice(scr, 2, replace=False):
    c = dm.loc[dm.USUBJID == lb.at[idx, "USUBJID"], "RFICDTC"].iloc[0]
    lb.at[idx, "LBDTC"] = iso(date.fromisoformat(c) - timedelta(days=4))

dm.to_csv("********\\dm.csv", index=False)
ae.to_csv("********\\ae.csv", index=False)
lb.to_csv("********\\lb.csv", index=False)
print(f"DM: {len(dm)} rows | AE: {len(ae)} rows | LB: {len(lb)} rows -> saved in data/")
