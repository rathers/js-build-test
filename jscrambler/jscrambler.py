# Copyright (c) 2013 Gustavo J. A. M. Carneiro  <gjcarneiro@gmail.com>

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



import requests
import urllib
from datetime import datetime
from collections import OrderedDict
import hashlib
import hmac
import base64

API_HOSTNAME = "api.jscrambler.com"
API_URL = "https://{0}/v3".format(API_HOSTNAME)


def _add_authentication(params, access_key, secret_key, method, request, signature_parameters=None):
    params.extend([
        ("access_key", access_key.encode("hex").upper()),
        ("timestamp", datetime.now().isoformat()),
        ])

    if signature_parameters is None:
        signature_parameters = params
    else:
        signature_parameters = params + signature_parameters

    signature_parameters.sort()

    url_query_string = '&'.join("{0}={1}".format(name, urllib.quote(value).replace("%7E", "~").replace("+", "%20")) for name, value in signature_parameters)
    hmac_signature_data = ';'.join([method, API_HOSTNAME, request, url_query_string])
    sig = hmac.new(secret_key.encode('hex').upper(), msg=hmac_signature_data, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(sig).decode()
    params.append(('signature', signature))


def post(access_key, secret_key, files, **opt_params):
    params = opt_params.items()
    sig_params = []
    files_dict = {}
    for num, fname in enumerate(files):
        m = hashlib.md5()
        m.update(open(fname, "rb").read())
        sig_params.append(("file_" + str(num), m.hexdigest().lower()))
        files_dict["file_" + str(num)] = (fname, open(fname, "rb"))
    _add_authentication(params, access_key, secret_key, "POST", "/code.json", signature_parameters=sig_params)
    r = requests.post(API_URL + "/code.json", data=OrderedDict(sorted(params)), files=files_dict)
    return r.json()


def get_status(access_key, secret_key, status=None, offset=None, limit=None, **opt_params):
    params = opt_params.items()
    if status is not None:
        params.append(('status', str(status)))
    if offset is not None:
        params.append(('offset', str(offset)))
    if limit is not None:
        params.append(('limit', str(limit)))
    _add_authentication(params, access_key, secret_key, "GET", "/code.json")
    r = requests.get(API_URL + "/code.json", params=OrderedDict(sorted(params)))
    return r.json()


def get_project_status(access_key, secret_key, project_id, symbol_table=None, **opt_params):
    request = '/code/{0}.json'.format(project_id)
    params = opt_params.items()
    if symbol_table is not None:
        params.append(('symbol_table', str(symbol_table)))
    _add_authentication(params, access_key, secret_key, "GET", request)
    r = requests.get(API_URL + request, params=OrderedDict(sorted(params)))
    return r.json()


def get_project_zip(access_key, secret_key, project_id, output_file, **opt_params):
    """
    output_file: a file name or file object
    """
    request = '/code/{0}.zip'.format(project_id)
    params = opt_params.items()
    _add_authentication(params, access_key, secret_key, "GET", request)
    r = requests.get(API_URL + request, params=OrderedDict(sorted(params)))
    if r.status_code == requests.codes.ok:
        if isinstance(output_file, basestring):
            f = open(output_file, "wb")
            f.write(r.content)
            f.close()
        else:
            output_file.write(r.content)
    else:
        raise RuntimeError


def get_project_source_info(access_key, secret_key, project_id, source_id, **opt_params):
    request = '/code/{0}/{1}.json'.format(project_id, source_id)
    params = opt_params.items()
    _add_authentication(params, access_key, secret_key, "GET", request)
    r = requests.get(API_URL + request, params=OrderedDict(sorted(params)))
    return r.json()


def get_project_source(access_key, secret_key, project_id, source_id, extension, **opt_params):
    request = '/code/{0}/{1}.{2}'.format(project_id, source_id, extension)
    params = opt_params.items()
    _add_authentication(params, access_key, secret_key, "GET", request)
    r = requests.get(API_URL + request, params=OrderedDict(sorted(params)))
    return r.text


def delete_project(access_key, secret_key, project_id, **opt_params):
    request = '/code/{0}.json'.format(project_id)
    params = opt_params.items()
    _add_authentication(params, access_key, secret_key, "DELETE", request)
    r = requests.delete(API_URL + request, params=OrderedDict(sorted(params)))
    return r.json()


