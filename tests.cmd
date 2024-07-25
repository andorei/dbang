if [%1] == [] (
    set database=sqlite
) else (
    set database=%1
)

python ddiff.py conf\ddiff-test-%database% all
python dget.py -o csv conf\dget-test-%database% all
python dget.py -o json conf\dget-test-%database% all
python dget.py -o html conf\dget-test-%database% all
python dget.py -o xlsx conf\dget-test-%database% all
python dput.py conf\dput-test-%database% all
python dtest.py conf\dtest-test-%database% all
