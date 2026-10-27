import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.sparse import hstack, csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier

KNOWN = ["recon", "file_explore", "credential_hunt", "persistence_probe"]
N = 30

df = pd.read_csv("features.csv")
known = df[df.label.isin(KNOWN)].reset_index(drop=True)
sw = df[df.label.str.startswith("sweep_")].reset_index(drop=True)
m = sw.label.str.extract(r"sweep_(.+)_k(\d)")
sw["family"], sw["k"] = m[0], m[1].astype(int)
num_cols = [c for c in df.columns if c not in ("session", "label", "cmd_seq")]

def tok(s):
    return [c.strip() for c in s.split(";")]

rows, base = [], []
for seed in range(N):
    train, test = train_test_split(known, test_size=0.3, stratify=known.label, random_state=seed)
    vec = CountVectorizer(tokenizer=tok, lowercase=False, token_pattern=None).fit(train.cmd_seq)

    def X(d):
        return hstack([csr_matrix(d[num_cols].values.astype(float)), vec.transform(d.cmd_seq)]).tocsr()

    clf = RandomForestClassifier(n_estimators=200, oob_score=True, random_state=seed).fit(X(train), train.label)
    thr = np.nanpercentile(clf.oob_decision_function_.max(1), 5)

    pt = clf.predict_proba(X(test))
    base.append({"red": np.mean(pt.max(1) < thr),
                 "acc": np.mean(clf.classes_[pt.argmax(1)] == test.label.values)})

    ps = clf.predict_proba(X(sw))
    conf = ps.max(1)
    ok = clf.classes_[ps.argmax(1)] == sw.family.values
    for k in range(7):
        s = (sw.k == k).values
        rows.append({"k": k, "red": np.mean(conf[s] < thr), "acc": np.mean(ok[s]), "conf": conf[s].mean()})

res = pd.DataFrame(rows)
q = lambda p: (lambda x: x.quantile(p))
tab = res.groupby("k").agg(red=("red", "mean"), red_alt=("red", q(0.025)), red_ust=("red", q(0.975)),
                           acc=("acc", "mean"), conf=("conf", "mean")).round(3)
b = pd.DataFrame(base).mean().round(3)
print("Referans (bilinen test, yeni komut yok): red=%.3f  aile dogrulugu=%.3f" % (b.red, b.acc))
print("\nHer k seviyesinde 12 oturum (4 aile x 3 tekrar), %d model" % N)
print(tab)
res.to_csv("sweep_results.csv", index=False)

fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].plot(tab.index, tab.red, marker="o")
ax[0].fill_between(tab.index, tab.red_alt, tab.red_ust, alpha=0.2)
ax[0].set_xlabel("Yeni komut sayisi (6 komutluk oturumda)")
ax[0].set_ylabel("Reddedilme orani")
ax[1].plot(tab.index, tab.acc, marker="o", color="tab:green")
ax[1].set_xlabel("Yeni komut sayisi (6 komutluk oturumda)")
ax[1].set_ylabel("Aile tahmin dogrulugu")
for a in ax:
    a.set_ylim(0, 1.02)
    a.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("egri.png", dpi=150)
print("\negri.png kaydedildi")
