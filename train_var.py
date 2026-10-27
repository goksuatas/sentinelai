import numpy as np, pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier

KNOWN = ["recon", "file_explore", "credential_hunt", "persistence_probe"]
EASY = ["sysinfo_deep", "network_probe"]
HARD = ["hard_mix_net", "hard_mix_sys"]
VAR = ["var_" + k for k in KNOWN]
N = 30
TS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]

df = pd.read_csv("features.csv")
known = df[df.label.isin(KNOWN)].reset_index(drop=True)
groups_df = {
    "var": df[df.label.isin(VAR)].reset_index(drop=True),
    "hard": df[df.label.isin(HARD)].reset_index(drop=True),
    "easy": df[df.label.isin(EASY)].reset_index(drop=True),
}
num_cols = [c for c in df.columns if c not in ("session", "label", "cmd_seq")]

def tok(s):
    return [c.strip() for c in s.split(";")]

rows, sweep = [], []
for seed in range(N):
    train, test = train_test_split(known, test_size=0.3, stratify=known.label, random_state=seed)
    vec = CountVectorizer(tokenizer=tok, lowercase=False, token_pattern=None).fit(train.cmd_seq)
    vocab = set(vec.vocabulary_)

    def build(d):
        X = hstack([csr_matrix(d[num_cols].values.astype(float)), vec.transform(d.cmd_seq)]).tocsr()
        oov = d.cmd_seq.apply(lambda s: np.mean([c not in vocab for c in tok(s)])).values
        return X, oov

    Xtr, _ = build(train)
    built = {"clean": build(test)}
    for k, d in groups_df.items():
        built[k] = build(d)

    clf = RandomForestClassifier(n_estimators=200, oob_score=True, random_state=seed).fit(Xtr, train.label)
    thr = np.nanpercentile(clf.oob_decision_function_.max(1), 5)

    r = {}
    for k, (X, oov) in built.items():
        r["red_" + k] = np.mean(clf.predict_proba(X).max(1) < thr)
        for t in TS:
            sweep.append({"esik": t, "grup": k, "oran": np.mean(oov >= t)})
    rows.append(r)

res = pd.DataFrame(rows)
print("== Model guvenine gore RED orani (%d bolme) ==" % N)
print("clean = bilinen aile, yeni komut yok (yanlis alarm)")
print("var   = bilinen aile + 1-2 yeni komut (yanlis alarm olmali)")
print("hard  = yarisi bilinen yarisi yeni (reddedilmeli)")
print("easy  = tamamen yeni (reddedilmeli)")
print(pd.DataFrame({"ortalama": res.mean(), "alt_%2.5": res.quantile(0.025),
                    "ust_%97.5": res.quantile(0.975)}).round(3))

sw = pd.DataFrame(sweep).pivot_table(index="esik", columns="grup", values="oran", aggfunc="mean")
print("\n== Yeni-komut orani >= esik olan oturumlarin payi ==")
print(sw[["clean", "var", "hard", "easy"]].round(2))
