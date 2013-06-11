#! /usr/bin/python
# Copyright (c) 2013 Gustavo J. A. M. Carneiro <gjcarneiro@gmail.com>

# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Adapted by JScrambler - 2013

import jscrambler
import requests
import sys
import time
import json
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Obfuscate a JS file")
    parser.add_argument('filepath', metavar="filepath", help="Path to the javascript file you want to obfuscate")
    return parser.parse_args()

def obfuscate():
    args = parse_args()
    #import logging
    #logging.basicConfig(level=logging.DEBUG)

    config = json.load(open(os.path.join(os.path.dirname(__file__), "client.config.json"), "rt"))
    ak = config["connection"]["access_key"].decode("hex")
    sk = config["connection"]["secret_key"].decode("hex")
    jscrambler.API_HOSTNAME = config["connection"]["server"]
    api_port = int(config["connection"]["port"])
    if api_port != 443:
        jscrambler.API_URL = "http://{0}:{1}/v3".format(jscrambler.API_HOSTNAME, api_port)
    maximum_poll_retries = 10
    poll_pause = 5 # seconds
    delete_project_at_the_end = True

    source_file = os.path.abspath(args.filepath)

    print "pyjscrambler 1.0"
    print "Using address {}:{}".format(jscrambler.API_HOSTNAME, api_port)
    print "Trying to send project containing:", ", ".join(config["files"].values())
    try:
        print jscrambler.post(ak, sk, {source_file}, **config["parameters"])
    except requests.exceptions.ConnectionError:
        print "Couldnt connect to JScrambler server."
        sys.exit() 

    for dummy in range(1, maximum_poll_retries):
        time.sleep(poll_pause)
        statuses = "getstatus:", jscrambler.get_status(ak, sk, limit=1)
        print statuses
        if statuses[1][0]['finished_at'] is not None:
            for status in statuses[1]:
                project_id = status['id']
                print "Fetching project", status['id']
                projstat = jscrambler.get_project_status(ak, sk, project_id)
                source_ids = [s['id'] for s in projstat['sources']]
                #jscrambler.get_project_zip(ak, sk, project_id, project_id+".zip")
                for source_id in source_ids:
                    extension = jscrambler.get_project_source_info(ak, sk, project_id, source_id)['extension']
                    obfuscated_contents = jscrambler.get_project_source(ak, sk, project_id, source_id, extension)
                    file_path, file_extension = os.path.splitext(source_file)
                    open(file_path + '.obfuscated' + file_extension, 'wt').write(obfuscated_contents)

                if delete_project_at_the_end:
                    print "Deleting project from JScrambler server..."
                    jscrambler.delete_project(ak, sk, project_id)
                    print "Finished."
                    return
        else:
            print "Project not finished. Retrying..."

if __name__ == '__main__':
    obfuscate()


