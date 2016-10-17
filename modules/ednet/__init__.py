# Web2py settings
from gluon import *
from gluon import current
import os
import sys

#import_path = os.path.join(request.folder,'modules')
#if (import_path not in sys.path):
#    sys.path.append(import_path)
#    spath_imported = True


# from .info import __VERSION__
# from .util import Util
# from .sequentialguid import SequentialGUID
# from .appsettings import AppSettings
# from .ad import AD
# from .w2py import W2Py
# from .canvas import Canvas
# from .student import Student
# from .faculty import Faculty


from ednet.info import __VERSION__
from ednet.util import Util
from ednet.sequentialguid import SequentialGUID
from ednet.appsettings import AppSettings
from ednet.ad import AD
from ednet.w2py import W2Py
from ednet.canvas import Canvas
from ednet.student import Student
from ednet.faculty import Faculty