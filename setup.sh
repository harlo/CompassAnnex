OLD_DIR=`pwd`
if [ $# -eq 0 ]
then
	echo "no initial args"
	ANNEX_DIR=/home/danse/unveillance_remote
	ANACONDA_DIR=/home/danse/anaconda
	UV_SERVER_HOST="10.51.119.238"
	UV_UUID="danse-v1"
else
	ANNEX_DIR=$1
	ANACONDA_DIR=$2
	UV_SERVER_HOST=$3
	UV_UUID=$4
fi 

USER_CONFIG=$OLD_DIR/lib/Annex/conf/annex.config.yaml
cd $OLD_DIR/lib/Annex
./setup.sh $OLD_DIR $ANNEX_DIR $ANACONDA_DIR

sudo apt-get install -y subversion
svn checkout http://peepdf.googlecode.com/svn/trunk/ lib/peepdf

echo "alias peepdf='python "$OLD_DIR"/lib/Annex/lib/peepdf/peepdf.py'" >> ~/.bashrc
echo export UV_SERVER_HOST="'"$UV_SERVER_HOST"'" >> ~/.bashrc
echo export UV_UUID="'"$UV_UUID"'" >> ~/.bashrc
source ~/.bashrc

echo "**************************************************"
echo 'Installing stanford nlp'
NLP_TAG="stanford-corenlp-full-2014-01-04"
cd $OLD_DIR/lib/stanford-corenlp
wget http://nlp.stanford.edu/software/$NLP_TAG.zip
unzip $NLP_TAG.zip

echo nlp_server.path: $OLD_DIR/lib/stanford-corenlp >> $USER_CONFIG
echo nlp_server.port: 8887
echo nlp_server.pkd: $NLP_TAG

echo "**************************************************"
echo 'Initing git annex on '$ANNEX_DIR'...'
cd $ANNEX_DIR
git init
mkdir .git/hooks
cp $OLD_DIR/lib/Annex/post-receive .git/hooks
chmod +x .git/hooks/post-receive

git annex init "unveillance_remote"
git annex untrust web
git checkout -b master

echo "**************************************************"
echo "Installing other python dependencies..."
cd $OLD_DIR/lib/Annex/lib/Worker/Tasks
ln -s $OLD_DIR/Tasks/* .
ls -la

cd ../Models
ln -s $OLD_DIR/Models/* .
ls -la

cd $OLD_DIR
pip install --upgrade -r requirements.txt

cd $OLD_DIR/lib/Annex
echo vars_extras: $OLD_DIR/vars.json >> conf/annex.config.yaml
python unveillance_annex.py -firstuse