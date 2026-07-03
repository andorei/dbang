if [ "$1" = "" ]
then
    export DBANGDB=sqlite
else
    export DBANGDB=$1
fi

ddiff.py test/ddiff_test_$DBANGDB all
dget.py test/dget_test_$DBANGDB all
dput.py --force test/dput_test_$DBANGDB all
dtest.py test/dtest_test_$DBANGDB all
