if [%1] == [] (
    set database=sqlite
) else (
    set database=%1
)

python ddiff.py test\ddiff_test_%database% all
python dget.py test\dget_test_%database% all
python dput.py --force test\dput_test_%database% all
python dtest.py test\dtest_test_%database% all
