import csv, random, time
from datetime import datetime, timezone
import paramiko

HOST, PORT = "127.0.0.1", 2222
USER, PASSWORD = "root", "test123"

KNOWN = {
    "recon": ["whoami", "uname -a", "id", "hostname", "cat /etc/passwd", "ls", "pwd", "uname -r", "cat /etc/os-release"],
    "file_explore": ["pwd", "ls", "ls -la", "cd /tmp", "cd /var/log", "ls /var/log", "cat /etc/hostname", "ls /home", "ls /etc", "cd /home"],
    "credential_hunt": ["ls ~/.ssh", "cat /etc/shadow", "history", "env", "cat ~/.bash_history", "ls -la ~", "cat /etc/passwd", "ls /root"],
    "persistence_probe": ["crontab -l", "ls /etc/cron.d", "cat /etc/rc.local", "id", "ls /etc/init.d", "cat /etc/crontab", "ls /etc/systemd/system"],
}
UNKNOWN = {
    "sysinfo_deep": ["cat /proc/cpuinfo", "free -m", "df -h", "uptime", "ps aux", "lscpu", "cat /proc/meminfo", "w"],
    "network_probe": ["ifconfig", "ip a", "netstat -an", "cat /etc/hosts", "cat /etc/resolv.conf", "ss -tulpn", "arp -a"],
}

def run_session(label, pool):
    cmds = random.sample(pool, min(random.randint(4, 8), len(pool)))
    base = random.choice([0.3, 0.8, 1.5])
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD,
                   look_for_keys=False, allow_agent=False, timeout=10)
    src_port = client.get_transport().sock.getsockname()[1]
    start = datetime.now(timezone.utc).isoformat()
    chan = client.invoke_shell()
    time.sleep(1)
    for cmd in cmds:
        chan.send(cmd + "\n")
        time.sleep(random.uniform(base, base * 2))
        while chan.recv_ready():
            chan.recv(4096)
    chan.send("exit\n")
    time.sleep(0.5)
    client.close()
    return src_port, start

if __name__ == "__main__":
    repeats = 15
    plan = [(l, p) for l, p in {**KNOWN, **UNKNOWN}.items() for _ in range(repeats)]
    random.shuffle(plan)
    with open("labels.csv", "a", newline="") as f:
        w = csv.writer(f)
        for i, (label, pool) in enumerate(plan, 1):
            port, start = run_session(label, pool)
            w.writerow([port, label, start])
            f.flush()
            print(f"{i}/{len(plan)} {label}")
            time.sleep(1)
