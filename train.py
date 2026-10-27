import numpy as np, pandas as pd
from scipy.sparse import hstack, csr_matrix
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, roc_auc_score

SEED = 42
KNOWN = ["recon", "file_explore", "credential_hunt", "persistence_probe"]

df = pd.read_csv("features.csv")
known = df[df.label.isin(KNOWN)].reset_index(drop=True)
unknown = df[~df.label.isin(KNOWN)].reset_index(drop=True)
num_cols = [c for c in df.columns if c not in ("session", "label", "cmd_seq")]

train, test = train_test_split(known, test_size=0.3, stratify=known.label, random_state=SEED)

def tok(s):
    return [c.strip() for c in s.split(";")]

vec = CountVectorizer(tokenizer=tok, lowercase=False, token_pattern=None)
vec.fit(train.cmd_seq)
vocab = set(vec.vocabulary_)

def build(d):
    X = hstack([csr_matrix(d[num_cols].values.astype(float)), vec.transform(d.cmd_seq)]).tocsr()
    oov = d.cmd_seq.apply(lambda s: np.mean([c not in vocab for c in tok(s)])).values
    return X, oov

Xtr, _ = build(train)
Xte, oov_te = build(test)
Xun, oov_un = build(unknown)

clf = RandomForestClassifier(n_estimators=300, oob_score=True, random_state=SEED)
clf.fit(Xtr, train.label)

pred = clf.predict(Xte)
print("== Bilinen ailelerde siniflandirma ==")
print("Egitim: %d, test: %d oturum" % (len(train), len(test)))
print("Dogruluk: %.3f   Makro F1: %.3f" % (accuracy_score(test.label, pred),
      f1_score(test.label, pred, average="macro")))
print(pd.DataFrame(confusion_matrix(test.label, pred, labels=KNOWN), index=KNOWN, columns=KNOWN))

conf_te = clf.predict_proba(Xte).max(1)
conf_un = clf.predict_proba(Xun).max(1)
thr = np.nanpercentile(clf.oob_decision_function_.max(1), 5)

print("\n== Bilinmeyen davranis testi ==")
print("Guven esigi (egitim OOB'un %%5'lik dilimi): %.3f" % thr)
print("Bilinen test oturumlarindan kabul edilen: %.2f" % np.mean(conf_te >= thr))
for fam in unknown.label.unique():
    m = (unknown.label == fam).values
    print("%s -> yabanci diye reddedilen: %.2f  (ortalama guven %.2f)" % (fam, np.mean(conf_un[m] < thr), conf_un[m].mean()))

y = np.r_[np.zeros(len(conf_te)), np.ones(len(conf_un))]
print("\nAUROC (model guveni):       %.3f" % roc_auc_score(y, np.r_[1 - conf_te, 1 - conf_un]))
print("AUROC (bilinmeyen komut orani): %.3f" % roc_auc_score(y, np.r_[oov_te, oov_un]))
print("Bilinen testte ort. bilinmeyen komut orani: %.2f, yabanci ailelerde: %.2f" % (oov_te.mean(), oov_un.mean()))
