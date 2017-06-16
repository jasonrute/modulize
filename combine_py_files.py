import os.path

class burn_after_reading:
    """Return an empty list if already calculated."""

    def __init__(self, f):
        self.memo = set()
        self.f = f

    def __call__(self, *arg):
        if arg in self.memo:
            return []
        else:
            self.memo.add(arg) #Do this here to avoid infinite loops
            val = self.f(*arg)
            return val

#################
# Code snippets #
#################

fake_module_preamble_str = \
"""\
import sys
from types import ModuleType

class MockModule(ModuleType):
    def __init__(self, module_name, module_doc=None):
        ModuleType.__init__(self, module_name, module_doc)
        if '.' in module_name:
            package, module = module_name.rsplit('.', 1)
            get_mock_module(package).__path__ = []
            setattr(get_mock_module(package), module, self)

    def _set_class_(self, cls):
        self._cls_ = cls
        self.__doc__ = cls.__doc__

    def __getattr__(self, name):
        return getattr(self._cls_, name)

def get_mock_module(module_name):
    if module_name not in sys.modules:
        sys.modules[module_name] = MockModule(module_name)
    return sys.modules[module_name]

def modulize(module_name, dependencies=[]):
    for d in dependencies: get_mock_module(d)
    global __name__; stored_name, __name__ = __name__, module_name
    def wrapper(cls):
        get_mock_module(module_name)._set_class_(cls)
        global __name__; __name__ = stored_name
    return wrapper

##===========================================================================##
"""

main_section_str = \
"""\n
##----- Begin {file} {padded_dashes_0}##
{text}
##----- End {file} {padded_dashes_1}##
"""

package_section_str = \
"""
@modulize('{name}'{dependencies})
class _{short_name}:
    ##----- Begin {file} {padded_dashes_0}##
{text}
    ##----- End {file} {padded_dashes_1}##
    pass
"""

module_section_str = \
"""
@modulize('{name}'{dependencies})
class _{short_name}:
    ##----- Begin {file} {padded_dashes_0}##
{text}
    ##----- End {file} {padded_dashes_1}##
    pass
"""

def get_modules_from_import_line(line):
    line = line.strip()
    if line.startswith('import'):
        # import module1 as x, module2 as y, ...
        line = line[7:] # remove "import "
        for import_str in  line.split(","):
            module = import_str.split()[0]
            yield module

    elif line.startswith('from'):
        line = line[5:] # remove "from "
        module, names = [s.strip() for s in line.split(" import ")]
        yield module
        for name in [n.strip() for n in names.split(",")]:
            yield module + '.' + name # name is likely not a module, but it could be
    
    #else: # not an import statement

@burn_after_reading
def parse_import_structure(package_dir, file='__main__.py'):
    module_list = []
    dependencies = set()
    with open(package_dir + file, 'r') as f:
        for line in f:
            for module in get_modules_from_import_line(line):
                module_prefix = []
                for m in module.split('.'):
                    module_prefix += [m]
                    path_prefix =  "/".join(module_prefix)
                    if os.path.isfile(package_dir + path_prefix + '.py'):
                        module_list += parse_import_structure(package_dir, path_prefix + '.py')
                        dependencies.add(".".join(module_prefix))

                    elif os.path.isfile(package_dir + path_prefix + '/__init__.py'):
                        module_list += parse_import_structure(package_dir, path_prefix + '/__init__.py')
                        dependencies.add(".".join(module_prefix))
                        
    return module_list + [(file, dependencies)]

def combine_into_one_file(package_dir, main_file='__main__.py', out='_combined.py', verbose=True):
    module_list = parse_import_structure(package_dir, main_file)
    visited = set()

    with open(out, 'w') as combined:
        combined.write(fake_module_preamble_str)

        for file, dependencies in module_list:
            if verbose:
                print("...", file)
            with open(package_dir + file, 'r') as f:
                if file == main_file:
                    combined.write(main_section_str.format(text=f.read(),
                                                    file=main_file,
                                                    padded_dashes_0 = '-'*(63 - len(file)),
                                                    padded_dashes_1 = '-'*(65 - len(file))))
                
                elif file.endswith('__init__.py'):
                    path = file.replace('__init__.py','')
                    name = path.replace('/','.')[:-1]
                    visited.add(name)
                    dependencies = dependencies - visited
                    if dependencies:
                        dependencies = ", dependencies=" + str(list(sorted(dependencies)))
                    else:
                        dependencies = ''
                    short_name = name.split('.')[-1]
                    text = "    " + "\n    ".join(f.read().split('\n'))
                    combined.write(package_section_str.format(path=path, 
                                                    short_name = short_name,
                                                    name = name, 
                                                    file=file, 
                                                    text=text,
                                                    dependencies = dependencies,
                                                    padded_dashes_0 = '-'*(63 - len(file)),
                                                    padded_dashes_1 = '-'*(65 - len(file))))
                
                else:
                    name = file.replace('/','.').replace('.py','')
                    visited.add(name)
                    dependencies = dependencies - visited
                    if dependencies:
                        dependencies = ", dependencies=" + str(list(sorted(dependencies)))
                    else:
                        dependencies = ''
                    short_name = name.split('.')[-1]
                    text = "    " + "\n    ".join(f.read().split('\n'))
                    combined.write(module_section_str.format(name=name, 
                                                    short_name = short_name,
                                                    file=file, 
                                                    text=text,
                                                    dependencies = dependencies,
                                                    padded_dashes_0 = '-'*(63 - len(file)),
                                                    padded_dashes_1 = '-'*(65 - len(file))))


if __name__ == '__main__':
    import sys # replace with argparser
    input_path = sys.argv[1] # entry file or directory
    output_file = sys.argv[2]

    if os.path.isfile(input_path):
        start_dir, start_file = os.path.split(input_path)
        combine_into_one_file(start_dir, start_file, out=output_file)
    elif os.path.isdir(input_path):
        start_dir = os.path.join(input_path, '') # puts in proper form with slash at end
        combine_into_one_file(start_dir, out=output_file) # my_file = '__main__.py'
    else:
        print("Improper input file/dir.")
        sys.exit(2)

    print("Sucessfully combined files.")
