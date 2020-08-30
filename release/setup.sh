#!/bin/bash -xv
set -e

# if [[ $EUID -ne 0 ]]; then
#    echo "This script must be run as root"
#    exit 1
# fi

# echo "This script is running as root $SUDO_USER"

if [[ $(lsb_release -rs) != "20.04" ]]; then
   echo "Non-compatible version"
   exit 2
fi

# strwho=$(who)
# #echo $string
# curuser=(`echo $strwho | tr ':' ' '` )  
# echo $curuser


sudo mkdir -p /opt/futuredial
sudo chown $USER:$USER /opt/futuredial
sudo mkdir -p /opt/futuredial/athena
sudo mkdir -p /opt/futuredial/hydradownloader
sudo chown $USER:$USER /opt/futuredial/athena
sudo chown $USER:$USER /opt/futuredial/hydradownloader
#chown athena:athena /opt/athena
#chown $SUDO_USER:$SUDO_USER /opt/athena

# echo add environment
if [[ -z $ATHENAHOME ]]; then 
   echo "set ATHENAHOME=/opt/futuredial/athena"
   export ATHENAHOME=/opt/futuredial/athena
   # echo 'export ATHENAHOME=/opt/futuredial/athena' >> /home/$curuser/.bashrc
   # source /home/$curuser/.bashrc
   echo 'export ATHENAHOME=/opt/futuredial/athena' >> ~/.bashrc
   source ~/.bashrc
fi

echo $ATHENAHOME
sudo apt install ssh redis -y

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
echo $serialnumber

echo "start downloading anthenacmc"
wget https://github.com/zytzjx/anthenacmc/raw/master/anthenacmc -O anthenacmc

cp ./anthenacmc $ATHENAHOME/anthenacmc
chmod +x $ATHENAHOME/anthenacmc

# $ATHENAHOME/anthenacmc -uuid=$serialnumber
# if [ $? -eq 0 ]; then
#   echo "Success: Serial Number is verified."
# else
#   echo "Failure: Serial Number can not be verify." >&2
#   exit 3
# fi

sudo apt install python3-pip python3-opencv python3-opencv-apps openjdk-11-jre-headless -y
sudo apt install gphoto2 libgphoto2-dev qt5-default python3-zbar zip unzip -y
sudo pip3 install gphoto2
sudo pip3 install redis
sudo pip3 install pyqt5 pyqtchart
sudo pip3 install pyserial
sudo pip3 install willow imutils pandas scikit-image
sudo pip3 install pyzbar
sudo pip3 install python-stdnum JPype1 pyro4 psutil

# sudo usermod -a -G dialout $curuser
# sudo usermod -a -G tty $curuser

sudo usermod -a -G dialout $USER
sudo usermod -a -G tty $USER

# pip3 install gphoto2
# pip3 install redis
# pip3 install pyqt5 pyqtchart
# pip3 install pyserial
# pip3 install willow imutils pandas scikit-image
# pip3 install pyzbar
# pip3 install python-stdnum JPype1

# echo "Need reboot after finish."
#reboot

#download 
echo "start downloading the CMC config..."
cd $ATHENAHOME
$ATHENAHOME/anthenacmc -uuid=$serialnumber
if [ $? -eq 0 ]; then
  echo "Success: Serial Number is verified."
else
  echo "Failure: Serial Number can not be verify." >&2
  exit 3
fi

echo "start downloading hydradownload"
wget https://github.com/zytzjx/hydradownload/raw/master/hydradownload -O hydradownload
chmod +x hydradownload

wget https://raw.githubusercontent.com/zytzjx/hydradownload/master/release/autoupdater.py -O autoupdater.py
wget https://raw.githubusercontent.com/zytzjx/hydradownload/master/release/cmcdeployment.py -O cmcdeployment.py
python3 autoupdater.py
python3 cmcdeployment.py
# $ATHENAHOME/hydradownload -path=/opt/futuredial/hydradownloader
# if [ $? -eq 0 ]; then
#   echo "Success: hydradownloader."
#   fn=$(ls /opt/futuredial/hydradownloader/)
#   if [ ! -z $fn ]; then
#     cd /opt/futuredial/hydradownloader
#     unzip $fn -d $ATHENAHOME
#     rm -f $fn
#     cd $ATHENAHOME
#   fi
# fi
crontab $ATHENAHOME/download_cron
cp $ATHENAHOME/athena.desktop ~/Desktop/athena.desktop
chmod +0744 ~/Desktop/athena.desktop
gio set ~/Desktop/athena.desktop "metadata::trusted" true
#deploy

# create shortcut

echo "Need reboot after finish."
