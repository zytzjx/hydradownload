import os
import redis
import json
import time
import stat

r = redis.Redis()

r.publish("ui_channel", json.dumps({'message':'Start up...'}))
time.sleep(2)

r.publish("ui_channel", json.dumps({'message':'Detecting hardware...'}))
time.sleep(2)

r.publish("ui_channel", json.dumps({'message':'Prepare cameras...'}))
time.sleep(2)

# chmod +x transaction
fn = os.path.join(os.environ('ATHENAHOME'),'transaction')
st = os.stat(fn)
os.chmod(fn, st.st_mode | stat.S_IEXEC|stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH)

r.publish("ui_channel", json.dumps({'action':'close', 'errorcode':0}))
r.close()