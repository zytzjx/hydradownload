![](https://www.futuredial.com/wp-content/uploads/2020/02/futuredial-logo-color.svg)

### error code
* 1 update failed
* 8 create request data for next time failed
* 0 Success

### command line
./hydradownload


### redis Key
hydradownload.running = 1
hydradownload.status=complete
hydradownload.framework=[]
hydradownload.phonedll=[]
hydradownload.phonetip=[]



### detail
./update  is created if download. All data will save this folder
updatelist.json is temp file. verify download list

clientstatus.json is next time post data.

./hydradownload -path=/opt/futuredial/hydradownloader



