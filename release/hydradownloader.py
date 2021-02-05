import os
import json
import redis
import fcntl
import hashlib
import logging
import requests
import subprocess
from logging.handlers import RotatingFileHandler

athena_home = '/opt/futuredial/athena.release'
hydra_download_temp = '/opt/futuredial/hydradownload'
hydradownload_lock = os.path.join(athena_home, 'hydradownloader.lck')
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s(%(lineno)d) %(message)s')
logFile = os.path.join(athena_home, 'hydradownloader.log')
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=50*1024*1024, backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)                                 
my_handler.setLevel(logging.INFO)
log = logging.getLogger('hydradownloader')
log.setLevel(logging.INFO)
log.addHandler(my_handler)
log.addHandler(logging.StreamHandler())

def get_host_uuid():
    ret = ''
    fn = os.path.join(athena_home, 'machine-id')
    if os.path.exists(fn):
        with open(fn) as f:
            ret = f.readline().strip()
    return ret

def get_host_name():
    ret = ''
    p = subprocess.Popen(['hostname'], stdout=subprocess.PIPE)
    x = p.communicate()
    if p.returncode==0:
        ret = x[0].decode().strip()
    return ret

def load_cmc_config():
    ret = {}
    ok = False
    log.info(f'load_cmc_config: ++ home={athena_home}')
    fn = os.path.join(athena_home, 'serialconfig.json')
    if os.path.exists(fn):
        with open(fn) as f:
            data = json.load(f)
            if 'ok' in data and data['ok'] == 1:
                if 'results' in data and isinstance(data['results'], list) and len(data['results'])>0:
                    ret = data['results'][0]
                    ok = True
    log.info(f'load_cmc_config: -- return {ok} dict={ret}')
    return ok, ret

def create_empty_cleint_sync(cmc_config):
    ret = {
        'client': {
            'company': cmc_config['companyid'],
            'site': cmc_config['siteid'],
            'solutionid': cmc_config['solutionid'],
            'productid': cmc_config['productid'],
            'pcname': get_host_name(),
            'macaddr': get_host_uuid()
        },
        'sync': {
            'status': {
                'framework': {
                    'version': '',
                    'filelist': []
                },
                'deviceprofile': {
                    'filelist': []
                }
            }
        },
        'protocol': '2.0'
    }
    return ret

def load_client_sync(cmc_config):
    ok = False
    log.info(f'load_client_sync: ++ home={athena_home}')
    fn = os.path.join(athena_home, 'clientsync.json')
    client_sync = {}
    if not os.path.exists(fn):
        client_sync = create_empty_cleint_sync(cmc_config)
        with open(fn, 'w') as f:
            json.dump(client_sync, f)
    if os.path.exists(fn):
        with open(fn) as f:
            client_sync = json.load(f)
            ok = True
    else:
        client_sync = create_empty_cleint_sync(cmc_config)
        ok = True
    log.info(f'load_client_sync: -- return {ok} dict={client_sync}')
    return ok, client_sync

def cmc_check_in(url, client_sync):
    ok = False
    resp = {}
    log.info(f'cmc_check_in: ++ url={url}, data={client_sync}')
    r = requests.post(f'{url}update/', json=client_sync)
    if bool(r) and r.status_code==200:
        resp = r.json()
        ok = True
    else: 
        log.error(f'Fail to post to server: {r}')
    log.info(f'cmc_check_in: ++ ok={ok}, resp={resp}')        
    return ok, resp

def download_file(remote, local):
    ok = False
    log.info(f'download_file: ++ remote={remote}, local={local}')
    url = remote['url'] if 'url' in remote else ''
    if bool(url):
        skip_download = False
        sz = remote['size'] if 'size' in remote else ''
        md5 = remote['checksum'] if 'checksum' in remote else ''
        if os.path.exists(local):
            if os.path.getsize(local) == int(sz):
                with open(local, 'rb') as f:
                    bs = f.read()
                    h = hashlib.md5(bs).hexdigest()
                    if md5.lower() == h.lower():
                        skip_download = True
        if skip_download:
            log.info(f'download_file: {local} existing already. Skip downloading.')        
            ok = True
        else:
            # download
            os.system(f'wget {url} -O {local}')
            if os.path.getsize(local) == int(sz):
                with open(local, 'rb') as f:
                    bs = f.read()
                    h = hashlib.md5(bs).hexdigest()
                    if md5.lower() == h.lower():
                        ok = True
                    else:
                        log.error(f'download_file: ERROR checksum incorrect.')                    
            else:
                log.error(f'download_file: ERROR size incorrect.')                    
    else:
        log.error(f'download_file: ERROR missing url')    
    log.info(f'download_file: -- return={ok}')
    return ok

def handle_framework(data):
    global rc
    ok = False
    log.info(f'handle_framework: ++ data={data}')
    if 'deletelist' in data:
        pass
    if 'filelist' in data and isinstance(data['filelist'], list):
        if len(data['filelist']) > 0:
            fd = data['filelist'][0]
            url = fd['url'] if 'url' in fd else ''
            if bool(url):
                fn = os.path.basename(url)
                local_fn = os.path.join(hydra_download_temp, fn)
                ok = download_file(fd, local_fn)
                if ok:
                    x = rc.get('hd.framework')
                    if bool(x) and os.path.exists(x):
                        if x != local_fn:
                            os.remove(x)
                    rc.set('hd.framework', local_fn)
                    x = json.dumps(data) 
                    rc.set('hd.framework.info', x)                   
        else:
            log.info(f'handle_framework: up to date.')            
            ok = True
    log.info(f'handle_framework: -- return ={ok}')
    return ok

def handle_setings(data):
    log.info(f'handle_setings: ++ data={data}')
    pass

def handle_deviceprofile(data):
    global rc
    log.info(f'handle_deviceprofile: ++ data={data}')
    all_ok = True
    if 'filelist' in data and isinstance(data['filelist'], list):
        for fd in data['filelist']:
            url = fd['url'] if 'url' in fd else ''
            if bool(url):
                fn = os.path.basename(url)
                local_fn = os.path.join(hydra_download_temp, fn)
                ok = download_file(fd, local_fn)
                all_ok &= ok
                if ok:
                    fd['local'] = local_fn
    if all_ok:
        fn = os.path.join(hydra_download_temp, 'deviceprofile.json')
        with open(fn, 'w') as f:
            json.dump(data, f)
    pass

def start_download():
    handler = {
        'framework': handle_framework,
        'settings': handle_setings,
        'deviceprofile': handle_deviceprofile,
    }
    os.makedirs(hydra_download_temp, exist_ok=True)
    ok, cmc_config = load_cmc_config()
    ok, client_sync = load_client_sync(cmc_config)
    url = cmc_config['webserviceserver']
    ok, resp = cmc_check_in(url, client_sync)
    if ok and bool(resp):
        for k in handler:
            if k in resp:
                handler[k](resp[k])
    pass

if __name__ == '__main__':
    global rc
    rc = redis.Redis(decode_responses=True)
    try:
        f = open(hydradownload_lock)
        fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        log.info('Another hydradownloader is running. Skip downloading')
    else:
        start_download()
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    finally:
        f.close()
    rc.close()
