OLD_DIR=`pwd`
if [ $# -eq 0 ]
then
	echo "no initial args"
	ANNEX_DIR=/media/rapture/Compass/V1/CompassAnnex
	ANACONDA_DIR=/home/minx/Packages/anaconda
	UV_SERVER_HOST="10.51.119.24"
	UV_UUID="compass-annex-rudydocs"
else
	ANNEX_DIR=$1
	ANACONDA_DIR=$2
	UV_SERVER_HOST=$3
	UV_UUID=$4
fi 

cd $OLD_DIR/lib/ANNEX_DIR
./setup.sh $OLD_DIR $ANNEX_DIR $ANACONDA_DIR

sudo apt-get install -y subversion
svn checkout http://peepdf.googlecode.com/svn/trunk/ lib/peepdf

echo "alias peepdf='python "$ANNEX_DIR"/lib/peepdf/peepdf.py'" >> .bashrc
echo export UV_SERVER_HOST="'"$UV_SERVER_HOST"'" >> .bashrc
echo export UV_UUID="'"$UV_UUID"'" >> .bashrc
source .bashrc

echo "**************************************************"
echo 'Initing git annex on '$ANNEX_DIR'...'
cd $ANNEX_DIR
git init
mkdir .git/hooks
cp $OLD_DIR/post-receive .git/hooks
chmod +x .git/hooks/post-receive

git annex init "unveillance_remote"
git annex untrust web
git checkout -b master

echo "**************************************************"
echo "Installing other python dependencies..."
cd $OLD_DIR
pip install --upgrade -r requirements.txt

cd lib/Annex/lib/Worker/Tasks
ln -s $OLD_DIR/Tasks/* .
ls -la

cd ../Models
ln -s $OLD_DIR/Models/* .
ls -la

cd $OLD_DIR/lib/Annex
python unveillance_annex.py -firstuse