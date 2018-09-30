# check_multi_url

## Intro

A nagios / icinga URL checking script written in Python 3 for mass-checking URLs asynchronously.

## Usage

	Usage: check_multi_url [options]

	Options:
	  -h, --help                                 show this help message and exit
	  -r RESULTSFILE, --resultsfile=RESULTSFILE  save full results in RESULTSFILE
	  -f RUNFILE, --runfile=RUNFILE              filename to save results
	  --log=LOGLEVEL                             Logging level

This script is executed with a "runfile" which is a YAML file listing the URLs & checks that are to be made on them. By default the check is for status code 200 to be returned. See the tests directory for some example runfiles or a simple one is below:

	---
	options:
	  - total_timeout: 20

	urls:
	  - url: http://www.bbc.co.uk
		test: code:301
	  - url: http://www.bbc.co.uk/doesntexist
	  - url: https://www.bbc.co.uk
		test: code:301
	  - url: http://slowwly.robertomurray.co.uk/delay/3000/url/http://www.google.co.uk
	  - url: http://httpbin.org/get
	  - url: https://api.ipify.org/
	  - url: http://slowwly.robertomurray.co.uk/delay/1000/url/http://bbc.co.uk
	  - url: http://no-dns-exists-for-myself.com/

As standard for nagios checks, it will exit with the appropriate return code and STDOUT text. If you enable the resultsfile, you'll get the full details of the check results stored on disk - note also that the results file can have a timestamp in the filename to store multiple runs, eg ```-r /tmp/prodrun.DATE```

## Dependencies

This makes heavy use of the [aiohttp](https://aiohttp.readthedocs.io/en/stable/) Python asynchronous HTTP request library which currently requires a minimum python version of 3.5.3.
