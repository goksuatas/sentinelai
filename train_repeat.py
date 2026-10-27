import numpy as np, pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

KNOWN = ["recon", "file_explore", "credential_hunt", "persistence_probe"]
EASY = ["sysinfo_deep", "network_probe"]
HARD = ["hard_mix_net", "hard_mix_sys"]
N = 30

df = pd.read_csv("features.csv")
known = df[df.label.isin(KNOWN)].reset_index(drop=True)
unknown = df[~df.label.isin(KNOWN)].reset_index(drop=True)
easy = unknown[unknown.label.isin(EASY)].reset_index(drop=True)
hard = unknown[unknown.label.isin(HARD)].reset_index(drop=True)
num_cols = [c for c in df.columns if c not in ("session", "label", "cmd_seq")]

def tok(s):
    return [c.strip() for c in s.split(";")]

rows = []
for seed in range(N):
    train, test = train_test_split(known, test_size=0.3, stratify=known.label, random_state=seed)
    vec = CountVectorizer(tokenizer=tok, lowercase=False, token_pattern=None).fit(train.cmd_seq)
    vocab = set(vec.vocabulary_)

    def build(d):
        X = hstack([csr_matrix(d[num_cols].values.astype(float)), vec.transform(d.cmd_seq)]).tocsr()
        oov = d.cmd_seq.apply(lambda s: np.mean([c not in vocab for c in tok(s)])).values
        return X, oov

    Xtr, _ = build(train)
    Xte, oov_te = build(test)
    Xe, oov_e = build(easy)
    Xh, oov_h = build(hard)

    clf = RandomForestClassifier(n_estimators=200, oob_score=True, random_state=seed).fit(Xtr, train.label)
    pred = clf.predict(Xte)
    thr = np.nanpercentile(clf.oob_decision_function_.max(1), 5)
    c_te, c_e, c_h = (clf.predict_proba(X).max(1) for X in (Xte, Xe, Xh))

    def auc(neg, pos):
        y = np.r_[np.zeros(len(neg)), np.ones(len(pos))]
        return roc_auc_score(y, np.r_[neg, pos])

    rows.append({
        "dogruluk": accuracy_score(test.label, pred),
        "makro_f1": f1_score(test.label, pred, average="macro"),
        "yanlis_alarm": np.mean(c_te < thr),
        "red_kolay": np.mean(c_e < thr),
        "red_zor": np.mean(c_h < thr),
        "auroc_guven_kolay": auc(1 - c_te, 1 - c_e),
        "auroc_guven_zor": auc(1 - c_te, 1 - c_h),
        "auroc_oov_kolay": auc(oov_te, oov_e),
        "auroc_oov_zor": auc(oov_te, oov_h),
    })

res = pd.DataFrame(rows)
out = pd.DataFrame({
    "ortalama": res.mean(),
    "alt_%2.5": res.quantile(0.025),
    "ust_%97.5": res.quantile(0.975),
}).round(3)
print("%d rastgele bolme, her biri 50 egitim / 22 test oturumu" % N)
print(out)
res.to_csv("repeat_results.csv", index=False)
