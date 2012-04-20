#!/usr/bin/env python

# Blofeld - All-in-one music server
# Copyright 2010 Dave Hayes <dwhayes@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301, USA.


import glob
import sys
import os
import shutil

# ModuleFinder can't handle runtime changes to __path__, but win32com uses them
try:
    # py2exe 0.6.4 introduced a replacement modulefinder.
    # This means we have to add package paths there, not to the built-in
    # one.  If this new modulefinder gets integrated into Python, then
    # we might be able to revert this some day.
    # if this doesn't work, try import modulefinder
    try:
        import py2exe.mf as modulefinder
    except ImportError:
        import modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]: #,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
except ImportError:
    # no build path setup, no worries.
    pass

from distutils.core import setup
import py2exe


sys.path.append(os.getcwd())

origIsSystemDLL = py2exe.build_exe.isSystemDLL
def isSystemDLL(pathname):
        if os.path.basename(pathname).lower() in ("sdl_ttf.dll", "libogg-0.dll"):
                return 0
        return origIsSystemDLL(pathname)
py2exe.build_exe.isSystemDLL = isSystemDLL

def delete_files(name):
    ''' Delete one file or set of files from wild-card spec '''
    for f in glob.glob(name):
        try:
            os.remove(f)
        except:
            print "Cannot remove file %s" % f
            exit(1)


def check_path(name):
    if os.name == 'nt':
        sep = ';'
        ext = '.exe'
    else:
        sep = ':'
        ext = ''

    for path in os.environ['PATH'].split(sep):
        full = os.path.join(path, name+ext)
        if os.path.exists(full):
            return name+ext
    print "Sorry, cannot find %s%s in the path" % (name, ext)
    return None


def pair_list(src):
    """ Given a list of files and dirnames,
        return a list of (destn-dir, sourcelist) tuples.
        A file returns (path, [name])
        A dir returns for its root and each of its subdirs
            (path, <list-of-file>)
        Always return paths with Unix slashes.
        Skip all SVN elements, .bak .pyc .pyo and *.~*
    """
    lst = []
    for item in src:
        if item.endswith('/'):
            for root, dirs, files in os.walk(item.rstrip('/\\')):
                path = root.replace('\\', '/')
                flist = []
                for file in files:
                    if not (file.endswith('.bak') or file.endswith('.pyc') or file.endswith('.pyo') or '~' in file):
                        flist.append(os.path.join(root, file).replace('\\','/'))
                if flist:
                    lst.append((path, flist))
        else:
            path, name = os.path.split(item)
            items = []
            items.append(name)
            lst.append((path, items))
    return lst


def unix2dos(name):
    """ Read file, remove \r, replace \n by \r\n and write back """
    base, ext = os.path.splitext(name)
    if ext.lower() not in ('.py', '.txt', '.css', '.js', '.tmpl', '.sh', '.cmd'):
        return

    print name
    try:
        f = open(name, 'rb')
        data = f.read()
        f.close()
    except:
        print "File %s does not exist" % name
        exit(1)
    data = data.replace('\r', '')
    data = data.replace('\n', '\r\n')
    try:
        f = open(name, 'wb')
        f.write(data)
        f.close()
    except:
        print "Cannot write to file %s" % name
        exit(1)


def rename_file(folder, old, new):
    try:
        oldpath = "%s/%s" % (folder, old)
        newpath = "%s/%s" % (folder, new)
        if os.path.exists(newpath):
            os.remove(newpath)
        os.rename(oldpath, newpath)
    except WindowsError:
        print "Cannot create %s" % newpath
        exit(1)


print sys.argv[0]

zip_cmd = check_path('zip')
unzip_cmd = check_path('unzip')
if os.name == 'nt':
    nsis_cmd = check_path('makensis')
else:
    nsis_cmd = '-'

if not (zip_cmd and unzip_cmd and nsis_cmd):
    exit(1)

if len(sys.argv) < 2:
    target = None
else:
    target = sys.argv[1]

if target not in ('binary', 'installer'):
    print 'Usage: buildwin32.py binary|installer'
    exit(1)


release = "0.01"

prod = 'racer-' + release
w32_service_name = 'racer-service.exe'
w32_console_name = 'racer-console.exe'
w32_window_name  = 'racer.exe'
w32_temp_name    = 'racer-windows.exe'

file_ins = prod + '-win32-setup.exe'
file_bin = prod + '-win32-bin.zip'

# List of data elements, directories end with a '/'


options = dict(
      name = 'Racer',
      version = release,
      author = 'Dave Hayes',
      author_email = 'dwhayes@gmail.com',
      scripts = ['racer.py'], 
      platforms = ['posix'],
      license = 'GNU General Public License 2 (GPL2)'
)

options['description'] = 'racer' + release

sys.argv[1] = 'py2exe'
program = [ {'script' : 'racer.py' } ]
options['options'] = {"py2exe":
                            {
                            "bundle_files": 1,
                            "packages": ["pygame"],
                            "excludes": ["pywin", "pywin.debugger", "pywin.debugger.dbgcon", "pywin.dialogs",
                                            "pywin.dialogs.list", "Tkconstants", "Tkinter", "tcl"],
                            "optimize": 2,
                            "dll_excludes": [ "kernelbase.dll", "powrprof.dll" ],
                            "compressed": 1
                            }
                        }
options['zipfile'] = None
#options['data_files'] = [("", ["DroidSansMono.ttf"])]


############################
# Generate the console-app
options['console'] = program
setup(**options)
rename_file('dist', w32_window_name, w32_console_name)


# Make sure that the root files are DOS format



############################
# Generate the windowed-app
options['windows'] = program
#del options['data_files']
del options['console']
setup(**options)
rename_file('dist', w32_window_name, w32_temp_name)




# Give the Windows app its proper name
rename_file('dist', w32_temp_name, w32_window_name)

# for doc in ['AUTHORS', 'ChangeLog', 'COPYING', 'INSTALL', 'NEWS', 'README']:
    # try:
        # os.rename(os.path.abspath('dist/%s' % doc), 
                  # os.path.abspath('dist/%s.txt'% doc))
        # unix2dos(os.path.abspath('dist/%s.txt'% doc))
    # except:
        # os.remove(os.path.abspath('dist/%s' % doc))

############################
if target == 'installer':
    os.system('makensis.exe /v3 /D_PRODUCT=%s /D_FILE=%s scripts\NSIS_Installer.nsi' % (release, file_ins))

    delete_files(file_bin)
    os.rename('dist', prod)
    os.system('zip -9 -r -X %s %s' % (file_bin, prod))
    os.rename(prod, 'dist')
