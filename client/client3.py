import csv, random, time
from datetime import datetime, timezone
import paramiko
from client2 import KNOWN, UNKNOWN, HOST, PORT, USER, PASSWORD

def run(label, cmds):
    base = random.choice([0.3, 0.8, 1.5])
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, port=PORT, username=USER, password=PASSWORD,
              look_for_keys=False, allow_agent=False, timeout=10)
    src_port = c.get_transport().sock.getsockname()[1]
    start = datetime.now(timezone.utc).isoformat()
    ch = c.invoke_shell()
    time.sleep(1)
    for cmd in cmds:
        ch.send(cmd + "\n")
        time.sleep(random.uniform(base, base * 2))
        while ch.recv_ready():
            ch.recv(4096)
    ch.send("exit\n")
    time.sleep(0.5)
    c.close()
    return src_port, start

def make(label):
    if label == "hard_mix_net":
        cmds = random.sample(KNOWN["recon"], 3) + random.sample(UNKNOWN["network_probe"], 3)
    else:
        cmds = random.sample(KNOWN["file_explore"], 3) + random.sample(UNKNOWN["sysinfo_deep"], 3)
    random.shuffle(cmds)
    return cmds

if __name__ == "__main__":
    plan = ["hard_mix_net"] * 15 + ["hard_mix_sys"] * 15
    random.shuffle(plan)
    with open("labels.csv", "a", newline="") as f:
        w = csv.writer(f)
        for i, label in enumerate(plan, 1):
            port, start = run(label, make(label))
            w.writerow([port, label, start])
            f.flush()
            print(f"{i}/{len(plan)} {label}")
            time.sleep(1)
