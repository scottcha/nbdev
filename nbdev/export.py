#AUTOGENERATED! DO NOT EDIT! File to edit: dev/00_export.ipynb (unless otherwise specified).

__all__ = ['read_nb', 'check_re', 'is_export', 'find_default_export', 'export_names', 'extra_add', 'relative_import',
           'reset_nbdev_module', 'get_nbdev_module', 'save_nbdev_module', 'create_mod_file', 'add_init',
           'notebook2script', 'DocsTestClass']

#Cell
from .imports import *
from fastscript import *

#Cell
def read_nb(fname):
    "Read the notebook in `fname`."
    with open(Path(fname),'r', encoding='utf8') as f: return nbformat.reads(f.read(), as_version=4)

#Cell
def check_re(cell, pat, code_only=True):
    "Check if `cell` contains a line with regex `pat`"
    if code_only and cell['cell_type'] != 'code': return
    if isinstance(pat, str): pat = re.compile(pat, re.IGNORECASE | re.MULTILINE)
    return pat.search(cell['source'])

#Cell
_re_blank_export = re.compile(r"""
# Matches any line with #export or #exports without any module name:
^         # beginning of line (since re.MULTILINE is passed)
\s*       # any number of whitespace
\#\s*     # # then any number of whitespace
exports?  # export or exports
\s*       # any number of whitespace
$         # end of line (since re.MULTILINE is passed)
""", re.IGNORECASE | re.MULTILINE | re.VERBOSE)

#Cell
_re_mod_export = re.compile(r"""
# Matches any line with #export or #exports with a module name and catches it in group 1:
^         # beginning of line (since re.MULTILINE is passed)
\s*       # any number of whitespace
\#\s*     # # then any number of whitespace
exports?  # export or exports
\s*       # any number of whitespace
(\S+)     # catch a group with any non-whitespace chars
\s*       # any number of whitespace
$         # end of line (since re.MULTILINE is passed)
""", re.IGNORECASE | re.MULTILINE | re.VERBOSE)

#Cell
def is_export(cell, default):
    "Check if `cell` is to be exported and returns the name of the module to export it if provided"
    if check_re(cell, _re_blank_export):
        if default is None:
            print(f"This cell doesn't have an export destination and was ignored:\n{cell['source'][1]}")
        return default
    tst = check_re(cell, _re_mod_export)
    return os.path.sep.join(tst.groups()[0].split('.')) if tst else None

#Cell
_re_default_exp = re.compile(r"""
# Matches any line with #default_exp with a module name and catches it in group 1:
^            # beginning of line (since re.MULTILINE is passed)
\s*          # any number of whitespace
\#\s*        # # then any number of whitespace
default_exp  # export or exports
\s*          # any number of whitespace
(\S+)        # catch a group with any non-whitespace chars
\s*          # any number of whitespace
$            # end of line (since re.MULTILINE is passed)
""", re.IGNORECASE | re.MULTILINE | re.VERBOSE)

#Cell
def find_default_export(cells):
    "Find in `cells` the default export module."
    for cell in cells:
        tst = check_re(cell, _re_default_exp)
        if tst: return tst.groups()[0]

#Cell
_re_typedispatch_func = re.compile(r"""
# Catches any function decorated with @typedispatch
(@typedispatch  # At any place in the cell, catch a group with something that begins with @patch
\s*def          # Any number of whitespace (including a new line probably) followed by def
\s+             # One whitespace or more
[^\(]*          # Anything but whitespace or an opening parenthesis (name of the function)
\s*\(           # Any number of whitespace followed by an opening parenthesis
[^\)]*          # Any number of character different of )
\)\s*:)         # A closing parenthesis followed by whitespace and :
""", re.VERBOSE)

#Cell
_re_class_func_def = re.compile(r"""
# Catches any 0-indented function or class definition with its name in group 1
^              # Beginning of a line (since re.MULTILINE is passed)
(?:def|class)  # Non-catching group for def or class
\s+            # One whitespace or more
([^\(\s]*)     # Catching group with any character except an opening parenthesis or a whitespace (name)
\s*            # Any number of whitespace
(?:\(|:)       # Non-catching group with either an opening parenthesis or a : (classes don't need ())
""", re.MULTILINE | re.VERBOSE)

#Cell
_re_obj_def = re.compile(r"""
# Catches any 0-indented object definition (bla = thing) with its name in group 1
^          # Beginning of a line (since re.MULTILINE is passed)
([^=\s]*)  # Catching group with any character except a whitespace or an equal sign
\s*=       # Any number of whitespace followed by an =
""", re.MULTILINE | re.VERBOSE)

#Cell
def _not_private(n):
    for t in n.split('.'):
        if (t.startswith('_') and not t.startswith('__')) or t.startswith('@'): return False
    return '\\' not in t and '^' not in t and '[' not in t

def export_names(code, func_only=False):
    "Find the names of the objects, functions or classes defined in `code` that are exported."
    #Format monkey-patches with @patch
    def _f(gps):
        nm, cls, t = gps.groups()
        if cls is not None: return f"def {cls}.{nm}():"
        return '\n'.join([f"def {c}.{nm}():" for c in re.split(', *', t[1:-1])])

    code = _re_typedispatch_func.sub('', code)
    code = _re_patch_func.sub(_f, code)
    names = _re_class_func_def.findall(code)
    if not func_only: names += _re_obj_def.findall(code)
    return [n for n in names if _not_private(n)]

#Cell
_re_all_def   = re.compile(r"""
# Catches a cell with defines \_all\_ = [\*\*] and get that \*\* in group 1
^_all_   #  Beginning of line (since re.MULTILINE is passed)
\s*=\s*  #  Any number of whitespace, =, any number of whitespace
\[       #  Opening [
([^\n\]]*) #  Catching group with anything except a ] or newline
\]       #  Closing ]
""", re.MULTILINE | re.VERBOSE)

#Same with __all__
_re__all__def = re.compile(r'^__all__\s*=\s*\[([^\]]*)\]', re.MULTILINE)

#Cell
def extra_add(code):
    "Catch adds to `__all__` required by a cell with `_all_=`"
    if _re_all_def.search(code):
        names = _re_all_def.search(code).groups()[0]
        names = re.sub('\s*,\s*', ',', names)
        names = names.replace('"', "'")
        code = _re_all_def.sub('', code)
        code = re.sub(r'([^\n]|^)\n*$', r'\1', code)
        return names.split(','),code
    return [],code

#Cell
def _add2add(fname, names, line_width=120):
    if len(names) == 0: return
    with open(fname, 'r', encoding='utf8') as f: text = f.read()
    tw = TextWrapper(width=120, initial_indent='', subsequent_indent=' '*11, break_long_words=False)
    re_all = _re__all__def.search(text)
    start,end = re_all.start(),re_all.end()
    text_all = tw.wrap(f"{text[start:end-1]}{'' if text[end-2]=='[' else ', '}{', '.join(names)}]")
    with open(fname, 'w', encoding='utf8') as f: f.write(text[:start] + '\n'.join(text_all) + text[end:])

#Cell
def relative_import(name, fname):
    "Convert a module `name` to a name relative to `fname`"
    mods = name.split('.')
    splits = str(fname).split(os.path.sep)
    if mods[0] not in splits: return name
    i=len(splits)-1
    while i>0 and splits[i] != mods[0]: i-=1
    splits = splits[i:]
    while len(mods)>0 and splits[0] == mods[0]: splits,mods = splits[1:],mods[1:]
    return '.' * (len(splits)) + '.'.join(mods)

#Cell
#Catches any from nbdev.bla import something and catches nbdev.bla in group 1, the imported thing(s) in group 2.
_re_import = re.compile(r'^(\s*)from (' + Config().lib_name + '.\S*) import (.*)$')

#Cell
def _deal_import(code_lines, fname):
    def _replace(m):
        sp,mod,obj = m.groups()
        return f"{sp}from {relative_import(mod, fname)} import {obj}"
    return [_re_import.sub(_replace,line) for line in code_lines]

#Cell
_re_patch_func = re.compile(r"""
# Catches any function decorated with @patch, its name in group 1 and the patched class in group 2
@patch         # At any place in the cell, something that begins with @patch
\s*def         # Any number of whitespace (including a new line probably) followed by def
\s+            # One whitespace or more
([^\(\s]*)     # Catch a group composed of anything but whitespace or an opening parenthesis (name of the function)
\s*\(          # Any number of whitespace followed by an opening parenthesis
[^:]*          # Any number of character different of : (the name of the first arg that is type-annotated)
:\s*           # A column followed by any number of whitespace
(?:            # Non-catching group with either
([^,\s\(\)]*)  #    a group composed of anything but a comma, a parenthesis or whitespace (name of the class)
|              #  or
(\([^\)]*\)))  #    a group composed of something between parenthesis (tuple of classes)
\s*            # Any number of whitespace
(?:,|\))       # Non-catching group with either a comma or a closing parenthesis
""", re.VERBOSE)

#Cell
def reset_nbdev_module():
    "Create a skeletton for `_nbdev`"
    fname = Config().lib_path/'_nbdev.py'
    fname.parent.mkdir(parents=True, exist_ok=True)
    with open(fname, 'w') as f:
        f.write(f"#AUTOGENERATED BY NBDEV! DO NOT EDIT!")
        f.write('\n\n__all__ = ["index", "modules"]')
        f.write('\n\nindex = {}')
        f.write('\n\nmodules = []')

#Cell
def get_nbdev_module():
    "Reads `_nbdev`"
    try:
        spec = importlib.util.spec_from_file_location(f"{Config().lib_name}._nbdev", Config().lib_path/'_nbdev.py')
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    except:
        return {'index': {}, 'modules': []}

#Cell
_re_index_idx = re.compile(r'index\s*=\s*{[^}]*}')
_re_index_mod = re.compile(r'modules\s*=\s*\[[^\]]*\]')

#Cell
def save_nbdev_module(mod):
    "Save `mod` inside `_nbdev`"
    fname = Config().lib_path/'_nbdev.py'
    with open(fname, 'r') as f: code = f.read()
    t = ',\n         '.join([f'"{k}": "{v}"' for k,v in mod.index.items()])
    code = _re_index_idx.sub("index = {"+ t +"}", code)
    t = ',\n           '.join([f'"{f}"' for f in mod.modules])
    code = _re_index_mod.sub(f"modules = [{t}]", code)
    with open(fname, 'w') as f: f.write(code)

#Cell
def create_mod_file(fname, nb_path):
    "Create a module file for `fname`."
    fname.parent.mkdir(parents=True, exist_ok=True)
    with open(fname, 'w') as f:
        f.write(f"#AUTOGENERATED! DO NOT EDIT! File to edit: dev/{nb_path.name} (unless otherwise specified).")
        f.write('\n\n__all__ = []')

#Cell
def _notebook2script(fname, silent=False, to_dict=None):
    "Finds cells starting with `#export` and puts them into a new module"
    if os.environ.get('IN_TEST',0): return  # don't export if running tests
    fname = Path(fname)
    nb = read_nb(fname)
    default = find_default_export(nb['cells'])
    if default is not None:
        default = os.path.sep.join(default.split('.'))
        if to_dict is None: create_mod_file(Config().lib_path/f'{default}.py', fname)
    mod = get_nbdev_module()
    exports = [is_export(c, default) for c in nb['cells']]
    cells = [(i,c,e) for i,(c,e) in enumerate(zip(nb['cells'],exports)) if e is not None]
    for i,c,e in cells:
        fname_out = Config().lib_path/f'{e}.py'
        orig = ('#C' if e==default else f'#Comes from {fname.name}, c') + 'ell\n'
        code = '\n\n' + orig + '\n'.join(_deal_import(c['source'].split('\n')[1:], fname_out))
        # remove trailing spaces
        names = export_names(code)
        extra,code = extra_add(code)
        if to_dict is None: _add2add(fname_out, [f"'{f}'" for f in names if '.' not in f and len(f) > 0] + extra)
        mod.index.update({f: fname.name for f in names})
        code = re.sub(r' +$', '', code, flags=re.MULTILINE)
        if code != '\n\n' + orig[:-1]:
            if to_dict is not None: to_dict[fname_out].append((i, fname, code))
            else:
                with open(fname_out, 'a', encoding='utf8') as f: f.write(code)
        if f'{e}.py' not in mod.modules: mod.modules.append(f'{e}.py')
    save_nbdev_module(mod)

    if not silent: print(f"Converted {fname.name}.")
    return to_dict

#Cell
def add_init(path):
    "Add `__init__.py` in all subdirs of `path` containing python files if it's not there already"
    for p,d,f in os.walk(path):
        for f_ in f:
            if f_.endswith('.py'):
                if not (Path(p)/'__init__.py').exists(): (Path(p)/'__init__.py').touch()
                break

#Cell
def notebook2script(fname=None, silent=False, to_dict=False):
    "Convert `fname` or all the notebook satisfying `all_fs`."
    # initial checks
    if os.environ.get('IN_TEST',0): return  # don't export if running tests
    if fname is None:
        reset_nbdev_module()
        files = [f for f in Config().nbs_path.glob('*.ipynb') if not f.name.startswith('_')]
    else: files = glob.glob(fname)
    d = collections.defaultdict(list) if to_dict else None
    for f in sorted(files): d = _notebook2script(f, silent=silent, to_dict=d)
    if to_dict: return d
    else: add_init(Config().lib_path)

#Cell
class DocsTestClass:
    def test(): pass