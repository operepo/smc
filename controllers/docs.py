# -*- coding: utf-8 -*-
# try something like
def index(): return dict(message="hello from docs.py")


@auth.requires_membership("Import", "Administrators")
def winrm():
    out = ""
    return dict(out=out)

@auth.requires_membership("Import", "Administrators")
def ad():
    out = ""
    return dict(out=out)
