#!/usr/bin/env python3

from http import cookies
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import os.path
import re
import sys
import time
import urllib.request
import logging

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.setLevel(logging.INFO)

def main():
    config = json.loads(open(os.path.dirname(os.path.abspath(__file__)) + "/gratisdnstxtupdate.conf.json", "r").read())

    # Parse args
    add = False
    if "--add" in sys.argv:
        add = True
    remove = False
    if "--remove" in sys.argv:
        remove = True
    domain = sys.argv[sys.argv.index("--domain") + 1]
    txtrecord = sys.argv[len(sys.argv)-1]

    if not (add or remove):
        return

    # Do not follow HTTP redirects.
    class MyHTTPErrorProcessor(urllib.request.HTTPErrorProcessor):
        def http_response(self, request, response):
            return response
        https_response = http_response
    urllib.request.install_opener(urllib.request.build_opener(MyHTTPErrorProcessor))

    # Log in.
    log.info("Logging into admin.gratisdns.dk with username " + config["username"])
    postargs = urlencode({"action": "logmein", "login": config["username"], "password": config["password"]})
    req = Request("https://admin.gratisdns.com/", data=postargs.encode("ascii"))
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urlopen(req)
    if resp.getcode() != 302:
        raise "unexpected http code while logging in: " + str(resp.getcode())
    c = cookies.SimpleCookie()
    c.load(resp.info()["Set-Cookie"])
    orgid = c["ORGID"].value

    # Get record ID of the TXT record if it already exists.
    log.info("Checking if _acme-challenge TXT record already exists")
    getargs = urlencode({"action": "dns_primary_changeDNSsetup", "user_domain": domain})
    req = Request("https://admin.gratisdns.com/?" + getargs)
    req.add_header("Cookie", "ORGID=" + orgid)
    resp = urlopen(req)
    if resp.getcode() != 200:
        raise "unexpected http code while getting records for domain: " + str(resp.getcode())
    recordId = 0
    body = resp.read().decode("utf-8")
    p = body.find("<td>_acme-challenge." + domain + "</td>")
    if p == -1:
        log.info("_acme-challenge TXT record does not currently exist")
    else:
        # Trim to just the table row for the record of interest.
        body = body[p:]
        p = body.find("</tr>")
        body = body[:p]
        recordId = re.search("&id=(\\d+)", body).group(1)
        log.info("_acme-challenge TXT record found with ID " + recordId)


    # Delete the TXT record if it already exists.
    if recordId != 0:
        log.info("Deleting _acme-challenge TXT record")
        getargs = urlencode({"action": "dns_primary_delete_txt", "id": recordId, "user_domain": domain})
        req = Request("https://admin.gratisdns.com/?" + getargs)
        req.add_header("Cookie", "ORGID=" + orgid)
        resp = urlopen(req)
        if resp.getcode() != 200:
            raise "unexpected http code while deleting TXT record for domain: " + str(resp.getcode())

    if add:
        # Add TXT record.
        log.info("Adding _acme-challenge TXT record")
        getargs = urlencode({"action": "dns_primary_record_add_txt", "user_domain": domain})
        postargs = urlencode({"action": "dns_primary_record_added_txt", "user_domain": domain, "name": "_acme-challenge." + domain, "txtdata": txtrecord, "ttl": "60"})
        req = Request("https://admin.gratisdns.com/?" + getargs, data=postargs.encode("ascii"))
        req.add_header("Cookie", "ORGID=" + orgid)
        resp = urlopen(req)
        if resp.getcode() != 200:
            raise "unexpected http code while adding TXT record for domain: " + str(resp.getcode())

        # Give time for the new record to propagate.
        log.info("Waiting 30 minutes for the new DNS record to propagate")
        time.sleep(60*30)

if __name__ == "__main__":
    main()
