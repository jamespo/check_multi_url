from collections import namedtuple
from concurrent.futures._base import TimeoutError
import asyncio
import aiohttp
import logging
import os
import re
import time
import yaml
from optparse import OptionParser


DEBUG = os.getenv('DEBUG')


class MultiCheck():
    '''a set of URLs to check with parameters taken from defaults, CLI or
    from YAML source check file itself priority CLI > YAML > default'''

    def __init__(self):
        self.options = {}
        self.get_cli_options()  # update self.options with CLI args
        self.logger = MultiCheck._setup_logging(self.options['loglevel'])
        self.runfile_valid = self.parse_runfile()
        self._set_defaults()

    def _set_defaults(self):
        '''set default options if not already set'''
        defaults = {'total_timeout': 10,
                    'defaultcheck': 'code:200'}
        for k, v in defaults.items():
            self.options.setdefault(k, v)

    @staticmethod
    def _setup_logging(loglevel):
        '''create logging instance'''
        # default to ERROR if unknown loglevel passed
        llevel_n = getattr(logging, loglevel.upper(), logging.ERROR)
        logging.basicConfig(level=llevel_n)
        logger = logging.getLogger('check_multi_url')
        return logger

    def get_cli_options(self):
        '''get command line options & return OptionParser'''
        parser = OptionParser()
        parser.add_option("-r", "--resultsfile", dest="resultsfile")
        parser.add_option("-f", "--runfile", dest="runfile",
                          help="filename to save results")
        parser.add_option("--log", dest="loglevel", help="Logging level",
                          default='ERROR')
        opts, args = parser.parse_args()
        # set object attributes to CLI args
        for opt in [x.dest for x in parser._get_all_options()[1:]]:
            if getattr(opts, opt) is not None:
                self.options[opt] = getattr(opts, opt)

    def parse_runfile(self):
        '''parse runfile & create check object'''
        try:
            with open(self.options['runfile']) as f:
                self.runfile = yaml.safe_load(f)
            assert isinstance(self.runfile, dict)  # basic parse check
        except (KeyError, FileNotFoundError, AssertionError) as excep:
            self.logger.critical(excep)
            return False
        # set MultiCheck.options
        if self.runfile.get('options'):
            for opt in self.runfile['options']:
                # convert single item dict to key & value & set in self.options
                self.options.setdefault(*list(opt.items())[0])
        return True

    def save_results(self):
        '''save results to YAML file if filename defined'''
        resultsfile = self.options.get('resultsfile')
        if resultsfile[-5:] == '.DATE':
            # timestamp resultsfilename by replacing .DATE
            resultsfile = resultsfile[:-4] + str(self.nowtime())
        try:
            with open(resultsfile, 'w') as rf:
                rf.write(yaml.dump(self.runfile))
        except:
            self.logger.error("Can't write to %s" % resultsfile)


class CheckRunner():
    '''take MultiCheck obj, get urls & check them, updating obj'''

    def __init__(self, mco):
        self.results = []
        self.mco = mco    # MultiCheck
        self.info = ''

    @staticmethod
    def check_result(result, test):
        '''individually check page result - takes FetchResult & test'''
        checktype, checkmatch = test.split(':', 1)
        if DEBUG:
            print('check_result: %s/%s' % (result, test))
        if checktype == 'code':
            # http status code check
            return int(checkmatch) == int(result.status)
        elif checktype == 're':
            # regexp match check
            search_res = re.search(checkmatch, result.text, re.MULTILINE)
            return search_res is not None
        elif checktype == 'duration':
            if checkmatch[0] == '<':
                # only less than supported for now
                return result.req_duration < float(checkmatch[1:])
        # unknown check?
        return False

    def check_all_results(self):
        '''check if results match tests - update runfile with results'''
        self.mco.runfile['checks_ok'] = 0
        self.mco.runfile['checks_completed'] = len(self.results)
        self.mco.runfile['checks_count'] = len(self.mco.runfile['urls'])
        # presumes result urls maintain order
        for result, urltest in zip(self.results, self.mco.runfile['urls']):
            # update check object with test result & time taken
            urltest['check_ok'], urltest['check_duration'] = result[:2]
            # add info field if not None
            if result[2] is not None:
                urltest['info'] = str(result[2])
                self.mco.logger.debug(urltest['info'])
            if urltest['check_ok']:
                self.mco.runfile['checks_ok'] += 1
            else:
                if self.info == '':
                    self.info = "Failed: %s" % (urltest['url'])
                else:
                    self.info += ", %s" % (urltest['url'])
        del self.results          # cleanup
        self.mco.logger.info(self.mco.runfile)

    @staticmethod
    async def fetch(url, test, session):
        '''fetch url async - returns test status, duration & info'''
        req_start_time = CheckRunner.nowtime()
        FetchResult = namedtuple('FetchResult', 'content status url req_duration')
        try:
            async with session.get(url, allow_redirects=False) as resp:
                content = await resp.text()
                check_duration = CheckRunner.nowtime(req_start_time)
                output = FetchResult(content, resp.status, url, check_duration)
                test_result = CheckRunner.check_result(output, test)
                if DEBUG:
                    print('fetch/status: %s' % resp.status)
                return test_result, check_duration, None
        except (aiohttp.client_exceptions.ClientConnectorError) as excep:
            return False, 0.0, excep

    async def mainloop(self):
        '''create tasks and wait for responses & update self.results'''
        jar = aiohttp.DummyCookieJar()
        timeout = aiohttp.ClientTimeout(total=self.mco.options['total_timeout'])
        tasks = []
        self.mco.runfile['start_time'] = self.nowtime()
        async with aiohttp.ClientSession(cookie_jar=jar,
                                         timeout=timeout) as session:
            # for url in [chk['url'] for chk in self.mco.runfile['urls']]:
            for chk in self.mco.runfile['urls']:
                # get defaultcheck if no test defined
                test = chk.get('test', self.mco.options['defaultcheck'])
                tasks.append(asyncio.ensure_future(self.fetch(chk['url'],
                                                              test, session)))
            try:
                self.results = await asyncio.gather(*tasks)
            except TimeoutError:
                # exceeded total_timeout
                error = 'Exceeded total timeout (%ss)' % \
                    self.mco.options['total_timeout']
                self.mco.logger.warning(error)
                self.info = error
        self.mco.runfile['finish_time'] = self.nowtime()  # needed?
        self.mco.runfile['duration'] = self.nowtime(self.mco.runfile['start_time'])

    @staticmethod
    def nowtime(start_time=0.0):
        '''returns the time as a float to 3dp or time diff if start_time provided'''
        return float("%0.3f" % (float(time.time() - start_time)))
