import csv, random, time
from datetime import datetime, timezone
import paramiko

HOST, PORT = "127.0.0.1", 2222
USER, PASSWORD = "root", "test123"

SCENARIOS = {
    "recon": ["whoami", "uname -a", "cat /etc/passwd", "ls"],
    "file_explore": ["pwd", "cd /tmp", "ls -la", "cat /etc/hostname", "ls /var/log"],
    "credential_hunt": ["ls ~/.ssh", "cat /etc/shadow", "history", "env"],
    "persistence_probe": ["crontab -l", "ls /etc/cron.d", "cat /etc/rc.local", "id"],
}

def run_session(label, commands):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD,
                   look_for_keys=False, allow_agent=False, timeout=10)
    src_port = client.get_transport().sock.getsockname()[1]
    start = datetime.now(timezone.utc).isoformat()
    chan = client.invoke_shell()
    time.sleep(1)
    for cmd in commands:
        chan.send(cmd + "\n")
        time.sleep(random.uniform(0.5, 2.0))
        while chan.recv_ready():
            chan.recv(4096)
    chan.send("exit\n")
    time.sleep(0.5)
    client.close()
    return src_port, start

if __name__ == "__main__":
    repeats = 3
    with open("labels.csv", "a", newline="") as f:
        w = csv.writer(f)
        for label, cmds in SCENARIOS.items():
            for _ in range(repeats):
                port, start = run_session(label, cmds)
                w.writerow([port, label, start])
                print(label, port)
                time.sleep(1)
