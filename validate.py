"""Run data validation checks (pandas) and produce mock data queries, like a Clinical Data Associate."""
import pandas as pd

dm = pd.read_csv("*******\\files\\data\\dm.csv")
ae = pd.read_csv("*******\\files\\data\\ae.csv")
lb = pd.read_csv("*******\\files\\data\\lb.csv")
queries = []

def add(check, domain, subj, var, issue, text):
    queries.append({"CHECK": check, "DOMAIN": domain, "USUBJID": subj,
                    "VARIABLE": var, "ISSUE": issue, "QUERY_TEXT": text})

# ---- Plausible physiological ranges (not normal ranges: values outside these are likely entry errors)
PLAUSIBLE = {"ALT": (1, 1000), "AST": (1, 1000), "CREAT": (0.1, 15), "HGB": (3, 25)}

# 1. Orphan records: AE subject not in DM
for _, r in ae[~ae.USUBJID.isin(dm.USUBJID)].iterrows():
    add("ORPHAN_SUBJECT", "AE", r.USUBJID, "USUBJID", "Subject not found in DM",
        f"Subject {r.USUBJID} has an AE record but is not in the demographics. Please confirm subject ID.")

# 2. Missing mandatory values
for _, r in ae[ae.AESEV.isna()].iterrows():
    add("MISSING_VALUE", "AE", r.USUBJID, "AESEV", "Severity missing",
        f"AE '{r.AETERM}' (start {r.AESTDTC}) has no severity. Please provide MILD/MODERATE/SEVERE.")
for _, r in lb[lb.LBORRES.isna()].iterrows():
    add("MISSING_VALUE", "LB", r.USUBJID, "LBORRES", "Lab result missing",
        f"{r.LBTESTCD} at {r.VISIT} has no result. Please provide the result or confirm test not done.")

# 3. Date logic
m = ae.merge(dm[["USUBJID", "RFICDTC"]], on="USUBJID")
for _, r in m[m.AESTDTC < m.RFICDTC].iterrows():
    add("DATE_BEFORE_CONSENT", "AE", r.USUBJID, "AESTDTC", "AE start before informed consent",
        f"AE '{r.AETERM}' starts {r.AESTDTC}, before consent date {r.RFICDTC}. Please verify the dates.")
for _, r in ae[ae.AEENDTC < ae.AESTDTC].iterrows():
    add("END_BEFORE_START", "AE", r.USUBJID, "AEENDTC", "AE end date before start date",
        f"AE '{r.AETERM}' ends {r.AEENDTC} but starts {r.AESTDTC}. Please correct.")
m = lb.merge(dm[["USUBJID", "RFICDTC"]], on="USUBJID")
for _, r in m[m.LBDTC < m.RFICDTC].iterrows():
    add("DATE_BEFORE_CONSENT", "LB", r.USUBJID, "LBDTC", "Lab collected before informed consent",
        f"{r.LBTESTCD} at {r.VISIT} collected {r.LBDTC}, before consent {r.RFICDTC}. Please verify.")

# 4. Duplicates
dups = ae[ae.duplicated(keep="first")]
for _, r in dups.iterrows():
    add("DUPLICATE_RECORD", "AE", r.USUBJID, "AETERM", "Exact duplicate AE record",
        f"AE '{r.AETERM}' starting {r.AESTDTC} appears more than once. Please confirm and remove duplicate.")

# 5. Range / plausibility
for _, r in dm[(dm.AGE < 18) | (dm.AGE > 100)].iterrows():
    add("RANGE_CHECK", "DM", r.USUBJID, "AGE", "Age outside eligibility/plausible range",
        f"Age is {r.AGE}; protocol requires 18+ and value must be plausible. Please verify.")
for code, (lo, hi) in PLAUSIBLE.items():
    bad = lb[(lb.LBTESTCD == code) & lb.LBORRES.notna() & ((lb.LBORRES < lo) | (lb.LBORRES > hi))]
    for _, r in bad.iterrows():
        add("IMPLAUSIBLE_VALUE", "LB", r.USUBJID, "LBORRES", f"{code} value physiologically implausible",
            f"{code} = {r.LBORRES} {r.LBORRESU} at {r.VISIT}. Please verify (possible transcription/unit error).")

q = pd.DataFrame(queries)
q.insert(0, "QUERY_ID", [f"Q{i:03d}" for i in range(1, len(q) + 1)])
q.to_csv("********\\files\\output\\mock_queries.csv", index=False)

print(f"Total queries raised: {len(q)}\n")
print(q.groupby(["DOMAIN", "CHECK"]).size().rename("COUNT").to_string())
print("\nQuery count by site (query burden):")
q["SITEID"] = q.USUBJID.str.split("-").str[1]
print(q.groupby("SITEID").size().rename("QUERIES").to_string())
