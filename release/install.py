import os
import json
import hashlib
import zipfile
import requests
import subprocess

def get_cmc_config():
    ret = {}
    fn = os.path.join(os.getcwd(), 'serialconfig.json')
    if os.path.exists(fn):
        with open(fn) as f:
            data = json.load(f)
            if 'ok' in data and data['ok'] == 1:
                if 'results' in data and len(data['results'])>0:
                    ret = data['results'][0]
    return ret

def get_framework(cmc_config, path):
    ret = False
    fn = ''
    post_data = {
        'client': {
            'company': cmc_config['companyid'],
            'solutionid': cmc_config['solutionid'],
            'productid': cmc_config['productid']
        },
        'sync': {
            'status':{
                'framework':{
                    'version': '',
                    'filelist': []
                }
            }
        },
        'protocol': '2.0'
    }
    url = cmc_config['webserviceserver']
    r = requests.post(f'{url}update/', json=post_data)
    resp = r.json()
    if 'framework' in resp:
        fl = resp['framework']['filelist']
        if len(fl)>0 :
            sz = fl[0]['size']
            md5 = fl[0]['checksum']
            url = fl[0]['url']
            fn = os.path.basename(url)
            fn = os.path.join(path, fn)
            if not os.path.exists(fn):
                os.system(f'wget {url} -O {fn}')
            if os.path.exists(fn):
                if os.path.getsize(fn) == int(sz):
                    with open(fn, 'rb') as f:
                        bs = f.read()
                        h = hashlib.md5(bs).hexdigest()
                        if md5.lower() == h.lower():
                            ret = True
    return ret, fn

def call_aptget(command):
    p = subprocess.run(['apt-get', 'update'])
    print(p)

def install():
    # call_aptget('')
    cmc_config = get_cmc_config()
    ret, fn = get_framework(cmc_config, os.getcwd())
    if ret and os.path.exists(fn):
        with zipfile.ZipFile(fn, 'r') as zip_ref:
            zip_ref.extractall(os.getcwd())
    os.remove(fn)
    # front-up flow
    fn = os.path.join(os.getcwd(), 'athena.frontup')
    fn1 = os.path.join(os.getcwd(), 'NPI')
    if os.path.exists(fn) and os.path.exists(fn1):
        os.symlink(fn1, os.path.join(fn,'NPI'), target_is_directory=True)
    fn1 = os.path.join(os.getcwd(), 'image_process')
    if os.path.exists(fn) and os.path.exists(fn1):
        os.symlink(fn1, os.path.join(fn,'image_process'), target_is_directory=True)
    os.makedirs(os.path.join(fn, 'history'), exist_ok=True)
    # back-up flow
    fn = os.path.join(os.getcwd(), 'athena.backup')
    fn1 = os.path.join(os.getcwd(), 'NPI')
    if os.path.exists(fn) and os.path.exists(fn1):
        os.symlink(fn1, os.path.join(fn,'NPI'), target_is_directory=True)
    fn1 = os.path.join(os.getcwd(), 'image_process')
    if os.path.exists(fn) and os.path.exists(fn1):
        os.symlink(fn1, os.path.join(fn,'image_process'), target_is_directory=True)
    os.makedirs(os.path.join(fn, 'history'), exist_ok=True)


if __name__=='__main__':
    install()
