if ($args.count -eq 0) {
    $database = 'sqlite'
} else {
    $database = $args[0]
}

python ddiff.py test\ddiff_test_$database all
python dget.py test\dget_test_$database all
python dput.py --force test\dput_test_$database all
python dtest.py test\dtest_test_$database all
