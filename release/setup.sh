#!/bin/bash -xv

set -e

if [[ $(lsb_release -rs) != "20.04" ]]; then
   echo "Non-compatible version"
   exit 2
fi

# if [[ $(id -u) -ne 0 ]] ; then 
#     echo "Please run as root" 
#     exit 1 
# fi

# create folder
sudo mkdir -p /opt/futuredial
sudo chown $USER:$USER /opt/futuredial
sudo mkdir -p /opt/futuredial/athena.release
sudo mkdir -p /opt/futuredial/hydradownloader
sudo chown $USER:$USER /opt/futuredial/athena.release
sudo chown $USER:$USER /opt/futuredial/hydradownloader
ATHENAHOME=/opt/futuredial/athena.release

# echo "input serial number"
# echo -e "\e[1;31mThis is red text\e[0m"
# echo "Please input this product SN:"
echo -e "\e[1;31mPlease input this product SN:\e[0m"
serialnumber=""
while read -r -n 1 key; do
   if [[ $key == "" ]]; then
      break
   fi
   # Add the key to the variable which is pressed by the user.
   serialnumber+=$key
done
echo 'Install Athena using serial number: ' $serialnumber

sudo apt-get update
sudo apt install python3-pip python3-opencv python3-opencv-apps openjdk-11-jre-headless -y
sudo apt install gphoto2 libgphoto2-dev qt5-default python3-zbar python3-serial zip unzip -y
sudo apt install nvidia-cuda-toolkit -y

sudo pip3 install gphoto2
sudo pip3 install redis
sudo pip3 install pyqt5 pyqtchart
sudo pip3 install pyserial
sudo pip3 install willow imutils pandas scikit-image
sudo pip3 install pyzbar exif
sudo pip3 install python-stdnum JPype1 pyro4 psutil
sudo pip3 install tensorflow==2.3.0

# cd /opt/futuredial/athena.release
cd $ATHENAHOME
id=$(sudo dmidecode -s system-uuid)
if [ -z "$id" ]
then
   id=$(uuidgen)
fi
echo $id | tee machine-id
touch hydradownloader.lck
touch athena.lck
touch cmcdeployment.lck

echo "start downloading CMC tool"
wget https://github.com/zytzjx/anthenacmc/raw/master/anthenacmc -O anthenacmc
chmod +x anthenacmc
./anthenacmc -uuid=$serialnumber
if [ $? -eq 0 ]; then
  echo "Success: Serial Number is verified."
else
  echo "Failure: Serial Number can not be verify." >&2
  exit 3
fi
# echo "start downloading CMC downloader"
# wget https://github.com/zytzjx/hydradownload/raw/master/hydradownload -O hydradownload
# chmod +x hydradownload
echo "start downloading Athena Framework and Unzip it"
wget https://raw.githubusercontent.com/zytzjx/hydradownload/master/release/hydradownloader.py
wget https://raw.githubusercontent.com/zytzjx/hydradownload/master/release/cmcdeployment.py
python3 hydradownloader.py
python3 cmcdeployment.py

# prepare desktop shortcut
cp $ATHENAHOME/athena_backup_flow.desktop ~/Desktop/
chmod +0744 ~/Desktop/athena_backup_flow.desktop
gio set ~/Desktop/athena_backup_flow.desktop "metadata::trusted" true

cp $ATHENAHOME/athena_frontup_flow.desktop ~/Desktop/
chmod +0744 ~/Desktop/athena_frontup_flow.desktop
gio set ~/Desktop/athena_frontup_flow.desktop "metadata::trusted" true

cp $ATHENAHOME/athenaCalibration.desktop ~/Desktop/
chmod +0744 ~/Desktop/athenaCalibration.desktop
gio set ~/Desktop/athenaCalibration.desktop "metadata::trusted" true

cp $ATHENAHOME/athenaTakePhotoBackup.desktop ~/Desktop/
chmod +0744 ~/Desktop/athenaTakePhotoBackup.desktop
gio set ~/Desktop/athenaTakePhotoBackup.desktop "metadata::trusted" true

cp $ATHENAHOME/AthenaTakePhotoFrontup.desktop ~/Desktop/
chmod +0744 ~/Desktop/AthenaTakePhotoFrontup.desktop
gio set ~/Desktop/AthenaTakePhotoFrontup.desktop "metadata::trusted" true

crontab $ATHENAHOME/download_cron
