#! /bin/bash
THIS_DIR=`pwd`

if [ $# -eq 0 ]
then
	echo "{}" > $THIS_DIR/lib/Annex/conf/compass.secrets.json
	WITH_CONFIG=$THIS_DIR/lib/Annex/conf/compass.secrets.json
else
	WITH_CONFIG=$1
fi

cd lib/Annex
./setup.sh $WITH_CONFIG
source ~/.bash_profile
echo $PATH
sleep 2

cd $THIS_DIR/lib/pyner
python setup.py install

cd $THIS_DIR

sudo apt-get install -y subversion
svn checkout http://peepdf.googlecode.com/svn/trunk/ lib/peepdf

python setup.py

cd $THIS_DIR/lib/Annex/lib/Worker/Tasks
ln -s $THIS_DIR/Tasks/* .
ls -la

cd ../Models
ln -s $THIS_DIR/Models/* .
ls -la

cd $THIS_DIR
pip install --upgrade -r requirements.txt

cd lib/Annex
chmod 0400 conf/*
python unveillance_annex.py -firstuse