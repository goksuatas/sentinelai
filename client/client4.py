import csv, random, time
from client2 import KNOWN
from client3 import run

NOVEL = ["date", "who", "last", "groups", "uname -m", "ls /opt", "cat /etc/issue",
         "ls /usr/bin", "cat /etc/group", "ls /srv", "cat /etc/motd", "echo $SHELL", "ls /mnt"]

def make(family):
    cmds = random.sample(KNOWN[family], 3) + random.sample(NOVEL, random.randint(1, 2))
    random.shuffle(cmds)
    return cmds

if __name__ == "__main__":
    plan = [f for f in KNOWN for _ in range(8)]
    random.shuffle(plan)
    with open("labels.csv", "a", newline="") as f:
        w = csv.writer(f)
        for i, fam in enumerate(plan, 1):
            port, start = run("var_" + fam, make(fam))
            w.writerow([port, "var_" + fam, start])
            f.flush()
            print(f"{i}/{len(plan)} var_{fam}")
            time.sleep(1)
