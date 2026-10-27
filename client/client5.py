import csv, random, time
from client2 import KNOWN
from client3 import run
from client4 import NOVEL

LEVELS = range(0, 7)
REPS = 3

def make(family, k):
    cmds = random.sample(KNOWN[family], 6 - k) + random.sample(NOVEL, k)
    random.shuffle(cmds)
    return cmds

if __name__ == "__main__":
    plan = [(f, k) for f in KNOWN for k in LEVELS for _ in range(REPS)]
    random.shuffle(plan)
    with open("labels.csv", "a", newline="") as f:
        w = csv.writer(f)
        for i, (fam, k) in enumerate(plan, 1):
            label = f"sweep_{fam}_k{k}"
            port, start = run(label, make(fam, k))
            w.writerow([port, label, start])
            f.flush()
            print(f"{i}/{len(plan)} {label}")
            time.sleep(1)
