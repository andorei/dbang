if [ "$1" = "" ]
then
    export DBANGDB=sqlite
else
    export DBANGDB=$1
fi

ddiff.py conf/ddiff-test-$DBANGDB all
dget.py conf/dget-test-$DBANGDB all
dput.py --force conf/dput-test-$DBANGDB all
dtest.py conf/dtest-test-$DBANGDB all
