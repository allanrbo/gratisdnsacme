# gratisdnsacme

Script to automate creation of _acme-challenge TXT records on gratisdns.dk.

Useful together with an ACME client that needs to do a dns-01 ACME challenge, such as [this version of acme_tiny.py](https://github.com/allanrbo/acme-tiny).

Signature: `gratisdnstxtupdate.py (--add|--remove) --domain DOMAIN -txtrecord TXTRECORD`

Example: `gratisdnstxtupdate.py --add --domain yoursite.com --txtrecord qLSh85v2W8MFIUWrCbx27FZM_LIfq6qvK5ulrowoxAA`

Requires a `gratisdnstxtupdate.conf.json` file in the same directory with this shape:
```
{
    "username": "...",
    "password": "..."
}
```
