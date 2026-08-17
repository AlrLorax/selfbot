import subprocess, threading, time, os, sys, httpx

WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')

def wh(content: str):
    if not WEBHOOK_URL:
        return
    try:
        httpx.post(WEBHOOK_URL, json={'content': content[:1990], 'username': 'VTG-LOG'}, timeout=10)
    except Exception:
        pass

def counts() -> str:
    parts = []
    for f in ('tkns.txt', 'locked.txt', 'unlocked.txt'):
        try:
            parts.append('%s: %d' % (f, sum(1 for _ in open(f, encoding='utf-8', errors='ignore'))))
        except Exception:
            parts.append('%s: 0' % f)
    return ' | '.join(parts)

start = time.time()
wh('**VTG iniciado** %s\nthreads=20 | proxies=200 residenciais | webhook vtg-logs' % time.strftime('%d/%m %H:%M:%S'))

proc = subprocess.Popen([sys.executable, '-u', 'main.py'],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        text=True, bufsize=1)

buf = []

def reader():
    with open('vtg.log', 'a', encoding='utf-8') as lf:
        for line in proc.stdout:
            line = line.rstrip('\n')
            buf.append(line)
            try:
                lf.write(line + '\n')
                lf.flush()
            except Exception:
                pass

threading.Thread(target=reader, daemon=True).start()

sent = 0
while proc.poll() is None:
    time.sleep(30)
    new = buf[sent:]
    if new:
        text = '\n'.join(new[-60:])
        text = text.encode('utf-8', 'replace').decode('utf-8', 'replace')[:1900]
        wh('**LOG** (%ds)\n%s\n```\n%s\n```' % (int(time.time() - start), counts(), text or '(sem output)'))
        sent = len(buf)
    else:
        wh('**heartbeat** (%ds) %s' % (int(time.time() - start), counts()))

wh('**VTG PAROU** (%ds) %s' % (int(time.time() - start), counts()))