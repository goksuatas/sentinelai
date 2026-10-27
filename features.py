import json
from pathlib import Path
import pandas as pd

HOME = Path.home() / "sentinelai"
LOG = HOME / "cowrie_all.json"
LABELS = HOME / "client" / "labels.csv"
OUT = HOME / "features.csv"

INFO = {"whoami", "uname", "id", "env", "hostname", "history"}
FS = {"ls", "cd", "cat", "pwd"}
SENSITIVE = ("shadow", ".ssh", "cron", "rc.local")

sessions = {}
with open(LOG) as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = e.get("session")
        if not sid:
            continue
        s = sessions.setdefault(sid, {"cmds": [], "times": [], "connect": None,
                                      "login": None, "dur": None, "fail": 0})
        ts = pd.to_datetime(e["timestamp"], utc=True)
        eid = e.get("eventid")
        if eid == "cowrie.session.connect":
            s["connect"] = ts
        elif eid == "cowrie.login.success":
            s["login"] = ts
        elif eid == "cowrie.login.failed":
            s["fail"] += 1
        elif eid == "cowrie.command.input":
            if e["input"].strip() != "exit":
                s["cmds"].append(e["input"].strip())
                s["times"].append(ts)
        elif eid == "cowrie.session.closed":
            s["dur"] = e.get("duration_ms")

rows = []
for sid, s in sessions.items():
    if s["connect"] is None:
        continue
    cmds = s["cmds"]
    first = [c.split()[0] if c.split() else "" for c in cmds]
    gaps = pd.Series(s["times"]).diff().dt.total_seconds().dropna()
    delay = (s["times"][0] - s["login"]).total_seconds() if cmds and s["login"] is not None else 0
    rows.append({
        "session": sid,
        "connect": s["connect"],
        "n_commands": len(cmds),
        "n_unique": len(set(cmds)),
        "duration_s": (s["dur"] or 0) / 1000,
        "first_cmd_delay": delay,
        "mean_gap": gaps.mean() if len(gaps) else 0,
        "std_gap": gaps.std() if len(gaps) > 1 else 0,
        "max_gap": gaps.max() if len(gaps) else 0,
        "n_info": sum(c in INFO for c in first),
        "n_fs": sum(c in FS for c in first),
        "n_sensitive": sum(any(k in c for k in SENSITIVE) for c in cmds),
        "login_fail": s["fail"],
        "cmd_seq": " ; ".join(cmds),
    })

df = pd.DataFrame(rows).sort_values("connect").reset_index(drop=True)
labels = pd.read_csv(LABELS, header=None, names=["port", "label", "start"])
labels["start"] = pd.to_datetime(labels["start"], utc=True)

if len(df) != len(labels):
    raise SystemExit(f"Sayilar uyusmuyor: log={len(df)} oturum, etiket={len(labels)} satir")

diff = (labels["start"] - df["connect"]).dt.total_seconds()
print("Zaman farki (sn)  min: %.2f  max: %.2f" % (diff.min(), diff.max()))
if diff.min() < -1 or diff.max() > 5:
    print("UYARI: eslesme supheli, zaman farklari beklenenden buyuk")

df["label"] = labels["label"]
df.drop(columns=["connect"]).to_csv(OUT, index=False)
print(df["label"].value_counts())
print(df.drop(columns=["connect", "session"]).head())
