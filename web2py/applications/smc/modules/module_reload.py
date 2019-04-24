import sys

MODULE_LIST = ["ednet.info",
               "ednet.util",
               "ednet.sequentialguid",
               "ednet.appsettings",
               "ednet.ad",
               "ednet.w2py",
               "ednet.canvas",
               "ednet.student",
               "ednet.faculty"
               ]


def ReloadModules():
    global MODULE_LIST

    # Web2py adds this prefix to modules
    prefix = "applications.smc.modules."
    msg = ""
    if sys.version_info[0] == 2:
        # Python 2
        # msg = "Detected Python2:"
        for m in MODULE_LIST:
            msg += "-- Reload: " + m + "  "
            module_name = prefix + m
            if module_name in sys.modules:
                try:
                    reload(sys.modules[module_name])
                except Exception as ex:
                    msg += str(ex)
            else:
                msg += "<- " + m + " not loaded yet"
    elif sys.version_info[0] == 3 and sys.version_info[1] < 4:
        # Python 3 < 3.4
        msg = "Detected < Python 3.4:"
        import imp
        for m in MODULE_LIST:
            msg += " - " + m
            imp.reload(m)
    elif sys.version_info[0] == 3 and sys.version_info[1] > 3:
        # Python 3 > 3.3
        msg = "Detected > Python 3.3: "
        import importlib
        for m in MODULE_LIST:
            msg += " - m"
            importlib.reload(m)
    else:
        msg = "Unknown Python?!?!? " + str(sys.version_info)

    return msg
