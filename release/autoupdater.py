import os
import json
import redis
import syslog
import subprocess

syslog.openlog('athena.autoupdater')
# downloader
athena_home = os.getenv("ATHENAHOME", '/opt/futuredial/athena')
os.putenv('ATHENAHOME', athena_home)
syslog.syslog('autoupdater: start downlaoding... {}'.format(athena_home))
fn = os.path.join(athena_home, 'hydradownload')
syslog.syslog('autoupdater: start downloand... {} '.format(fn))
if os.path.exists(fn):
    p = subprocess.Popen([fn], cwd=athena_home)
    p.wait()
    syslog.syslog('autoupdater: hydradownload return: {}'.format(p.returncode))
syslog.syslog('autoupdater: complete downloand.')

# deploy
syslog.syslog('autoupdater: start deployment ...')
r = redis.Redis()
athena_status = r.get('athena.status')
if bool(athena_status) and athena_status.decode('utf-8') == 'running':
    syslog.syslog('autoupdater: deployment postponed ...')
else:
    syslog.syslog('autoupdater: start deployment ...')
    fn = os.path.join(athena_home, 'cmcdeployment.py')
    p = subprocess.Popen(['python3', fn], cwd=athena_home)
    p.wait()
syslog.syslog('autoupdater: deployment complete ...')
syslog.closelog()