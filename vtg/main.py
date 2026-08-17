# VTG-V2 - Discord Account Creator (adaptado p/ GitHub Actions)
print("[ ! ] Loading Modules...\n")
from modules.console import Console
from modules.session import HttpSession
from modules.discord import DiscordApi, DiscordWs
from modules.captcha import CaptchaSolver
import random, threading, time, json, itertools, os, string

num = "115427"  # build number (testado: aceito pela API atual)

proxies = open("./proxies.txt", 'r+').read().splitlines()
config = json.load(open("./config.json"))

class Discord:
    def __init__(self) -> None:
        try:
            with open("./discord_usernamesd.txt", encoding="utf-8") as f:
                self.users = [i.strip() for i in f]
        except Exception:
            self.users = ["i love vast", "vast is cute", "vtg"]

    def GEN(self):
        Console._cap_worker += 1
        tentativas = 0
        while tentativas < 3:  # limite de retry por thread (sem recursao infinita)
            tentativas += 1
            try:
                self._username = random.choice(self.users)
                proxy = 'http://' + random.choice(proxies)

                session = HttpSession(proxy)
                Console.debug("[*] Created Session (\x1b[38;5;147m%s\x1b[0m)" % (
                    session.http_client.get("https://wtfismyip.com/text").text.strip("\n")))

                capkey = CaptchaSolver().get_captcha_by_ai(
                    proxy.split('://')[1], config['site_key'])

                if capkey == 'ERROR' or capkey is None:
                    Console._proxy_err += 1
                    Console.debug('[-] Proxy/Captcha Error | tentativa %d...' % tentativas)
                    continue

                session.get_cookies()
                if config["verify_email"]:
                    email = DiscordApi.genmail()
                else:
                    email = (0, "".join(random.choice(string.ascii_letters + string.digits)
                                        for _ in range(10)) + "@gmail.com")
                token = api_register(session.http_client, capkey, num, email[1], self._username)

                if 'token' in str(token):
                    Console.info('[/] Generated token: %s' % token['token'])
                    Console._generated += 1
                    with open("tkns.txt", "a") as f:
                        f.write('%s\n' % token['token'])
                    flags = DiscordApi.check_flag(session.http_client, token['token'])
                    if "Locked: \u2713" in str(flags):
                        Console.info('[/] LOCKED Token: %s' % token['token'])
                        with open("locked.txt", "a") as fp:
                            fp.write('%s\n' % token['token'])
                    else:
                        Console.info('[/] UNLOCKED token: %s' % token['token'])
                        if email[0] != 0:  # so legitamiza se tiver email de verdade
                            try:
                                DiscordApi.legitamize_account(
                                    session.http_client, token['token'], email[0], proxy)
                            except Exception as e:
                                Console.debug('[-] legitamize falhou: %s' % e)
                        else:
                            Console.debug('[*] sem email - conta unverified')
                        Console.info(flags)
                        with open("unlocked.txt", "a") as fp:
                            fp.write('%s\n' % token['token'])
                    DiscordWs(token).start()
                    break
                else:
                    Console.debug('[-] Register Error: %s' % token)

            except KeyboardInterrupt:
                raise
            except Exception:
                Console.debug('[-] Gen Exception | tentativa %d' % tentativas)
                continue

        Console._cap_worker -= 1

    def __start__(self):
        threading.Thread(target=Console.title_thread).start()
        while True:
            if threading.active_count() < int(config['threads']):
                threading.Thread(target=self.GEN).start()
                time.sleep(0.1)


# register isolado p/ capturar a resposta sem quebrar o fluxo
def api_register(client, captcha_key, build_num, email, _username):
    from modules.discord import Payload, DiscordApi
    payload = Payload.simple_register(_username, client.headers['x-fingerprint'],
                                      captcha_key, email)
    xsup = DiscordApi.get_trackers(build_num, False)
    client.headers['x-super-properties'] = xsup
    client.headers['content-length'] = str(len(__import__('json').dumps(payload)))
    client.headers['referer'] = 'https://discord.com/register'
    client.headers['X-Debug-Options'] = 'bugReporterEnabled'
    client.headers['X-Discord-Locale'] = 'en'
    r = client.post('https://discord.com/api/v10/auth/register', json=payload)
    try:
        return r.json()
    except Exception:
        return r.text


if __name__ == '__main__':
    Console.print_logo()
    Discord().__start__()