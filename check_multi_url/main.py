#!/usr/bin/env python3

# check_multi_url ; -*-Python-*-
# a simple nagios check to validate multiple URLs in parallel using async
# Copyright James Powell 2018 / jamespo [at] gmail [dot] com
# This program is distributed under the terms of the GNU General Public License v3

import asyncio
import sys
from check_multi_url import MultiCheck, CheckRunner


def cli():
    '''create options & check objects, run async loop & check results'''
    mco = MultiCheck()
    if not mco.runfile_valid:
        quit("Couldn't parse runfile", "", 3)
    cr = CheckRunner(mco)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(cr.mainloop())
    cr.check_all_results()
    if mco.options.get('resultsfile') is not None:
        mco.save_results()
    all_passed = mco.runfile['checks_ok'] == mco.runfile['checks_count']
    rc = (0 if all_passed else 2)
    quit('%s/%s checks passed' %
         (mco.runfile['checks_ok'], mco.runfile['checks_count']),
         cr.info, rc,
         'duration=%ss' % mco.runfile['duration'])


def quit(msg='', info='', status=0, perf_str=''):
    '''display msg & quit'''
    code2warn = {0: 'OK', 1: 'WARNING', 2: 'CRITICAL', 3: 'UNKNOWN'}
    if info != '':
        info = ' (%s)' % info
    print('%s: %s%s|%s' % (code2warn[status], msg, info, perf_str))
    sys.exit(status)
