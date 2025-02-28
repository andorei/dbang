if ($args.count -eq 0) {
    $database = 'sqlite'
} else {
    $database = $args[0]
}

python ddiff.py conf\ddiff-test-$database all
python dget.py conf\dget-test-$database all
python dput.py --force conf\dput-test-$database all
python dtest.py conf\dtest-test-$database all
