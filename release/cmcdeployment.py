import os
import sys
import json
import redis
import fcntl
import shutil
import zipfile
import logging
import tempfile
import subprocess
import configparser
from logging.handlers import RotatingFileHandler

athena_home = '/opt/futuredial/athena.release'
hydra_download_temp = '/opt/futuredial/hydradownload'
hydradownload_lock = os.path.join(athena_home, 'hydradownloader.lck')
athena_lock = os.path.join(athena_home, 'athena.lck')
deployment_lock = os.path.join(athena_home, 'cmcdeployment.lck')
log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s(%(lineno)d) %(message)s')
logFile = os.path.join(athena_home, 'cmcdeployment.log')
my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=50*1024*1024, backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)                                 
my_handler.setLevel(logging.INFO)
log = logging.getLogger('cmcdeployment')
log.setLevel(logging.INFO)
log.addHandler(my_handler)
log.addHandler(logging.StreamHandler())

def deploy_deviceprofile():
    log.info('deploy_deviceprofile: ++')
    fn = os.path.join(athena_home, 'deploydeviceprofile.py')
    if os.path.exists(fn):
        p = subprocess.Popen([sys.executable, fn], cwd=athena_home)
        p.wait()
    else:
        local_dp = []
        local_dp_by_readableid = {}
        npi_root = os.path.join(athena_home, 'NPI')
        # easy deploy first time
        fn = os.path.join(hydra_download_temp, 'deviceprofile.json')
        if os.path.exists(fn):
            with open(fn) as f:
                dp = json.load(f)
            # remove device profile fist
            if 'deletelist' in dp and isinstance(dp['deletelist'], list):
                for d in dp['deletelist']:
                    pass
            # add device profile
            if 'filelist' in dp and isinstance(dp['filelist'], list):
                for fd in dp['filelist']:
                    fn = fd['local'] if 'local' in fd else ''
                    if os.path.exists(fn):
                        npi_temp = tempfile.TemporaryDirectory(suffix='dp')
                        with zipfile.ZipFile(fn, 'r') as zip_ref:
                            zip_ref.extractall(npi_temp.name)
                        info_ini = configparser.ConfigParser()
                        info_ini.read(os.path.join(npi_temp.name, 'info.ini'))
                        folder = info_ini['information']['folder']
                        shutil.copyfile(os.path.join(npi_temp.name, 'info.ini'), os.path.join(npi_temp.name, 'resource', folder, 'info.ini'))
                        shutil.copytree(os.path.join(npi_temp.name, 'resource', folder), os.path.join(npi_root, folder), dirs_exist_ok=True)
                        npi_temp.cleanup()
                        os.remove(fn)
                        local_dp_by_readableid[fd['readableid']] = {
                            'folder': folder,
                        }
                        fd.pop('url', None)
                        fd.pop('local', None)
                        local_dp.append(fd)
            os.remove(os.path.join(hydra_download_temp, 'deviceprofile.json'))
        with open(os.path.join(npi_root, 'deviceprofile.json'), 'w') as f:
            json.dump({
                'syncclient': local_dp,
                'readableid': local_dp_by_readableid
            }, f)
        # update clientsync.json
        if len(local_dp) > 0:
            with open(os.path.join(athena_home, 'clientsync.json')) as f:
                cs = json.load(f)
            cs['sync']['status']['deviceprofile']['filelist'].clear()
            for dp in local_dp:
                cs['sync']['status']['deviceprofile']['filelist'].append(dp)
            with open(os.path.join(athena_home, 'clientsync.json'), 'w') as f:
                json.dump(cs, f)
    log.info('deploy_deviceprofile: --')

def deploy_frameword(rc):
    log.info('deploy_frameword: ++')
    ok = False
    fw_info = None
    x = rc.get('hd.framework.info')
    if bool(x):
        fw_info = json.loads(x)
        fn = rc.get('hd.framework')
        if os.path.exists(fn):
            with zipfile.ZipFile(fn, 'r') as zip_ref:
                zip_ref.extractall(athena_home)
            os.remove(fn)
            ok = True
            rc.delete('hd.framework.info')
            rc.delete('hd.framework')
    else:
        ok = True
    log.info(f'deploy_frameword: -- ret={ok} info={fw_info}')
    return ok, fw_info

def update_client_sync(fw_info):
    log.info(f'update_client_sync: ++ framework={fw_info}')
    fn = os.path.join(athena_home, 'clientsync.json')
    cs = {}
    with open(fn) as f:
        cs = json.load(f)
    # update framework version
    if bool(fw_info):
        ver = fw_info['version'] if 'version' in fw_info else ''
        cs['sync']['status']['framework']['version'] = ver
    ###
    # save clientsync.json
    with open(fn,'w') as f:
        json.dump(cs, f)
    log.info('update_client_sync: --')

def deploy():
    log.info('deploy: ++')
    rc = redis.Redis(decode_responses=True)
    fw_ok, fw_info = deploy_frameword(rc)
    # framework ok
    if fw_ok and bool(fw_info):
        update_client_sync(fw_info)
    # deploy deviceprofile
    deploy_deviceprofile()
    rc.close()
    log.info('deploy: --')    

if __name__ == '__main__':
    try:
        hd_lck = open(hydradownload_lock)
        athena_lck = open(athena_lock)
        deploy_lck = open(deployment_lock)
        fcntl.flock(hd_lck.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(athena_lck.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(deploy_lck.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except:
        log.info('Another hydradownloader is running. Skip deployment')
    else:
        deploy()
        fcntl.flock(hd_lck.fileno(), fcntl.LOCK_UN )
        fcntl.flock(athena_lck.fileno(), fcntl.LOCK_UN)
        fcntl.flock(deploy_lck.fileno(), fcntl.LOCK_UN)
    finally:
        hd_lck.close()
        athena_lck.close()
        deploy_lck.close()
    
