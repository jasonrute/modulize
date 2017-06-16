# Python Modulization #

This project contains three Python tools:

1. [A decorator `@modulize`](#modulize) which turns a class into a (mock) Python module which can then be imported:
	```python 
	@modulize('my_module')
	class my_dummy_class:
	    def my_function(s):
	        print(s, 'bar')

	from my_module import my_function
	my_function('foo') # foo bar
	```

2. [A Python script `combine_py_files.py`](#combine) which combines a `.py` file and all the local `.py` files it imports into one `.py` file. 

   The motivations for this tool are programming contests which require a single `.py` file.  This makes it is possible to break up a project into multiple files and combine them automatically in the end.

3. [A Python script `sync_combined_py_files.py`](#sync) which runs in the background, keeping track of changes to both the combined file and the source files, syncing changes between them. **(In progress)**

-----
## <a name="modulize"></a> `@modulize` decorator ##

### `@modulize(module_name, dependencies=[])` ###

The @modulize decorator (which can be found in `modulization.py`) works as follows:
```python 
# The code defining modulize is short and can be hard
# coded in place of this import line:
from modulization import modulize 

@modulize('a')
class dummy_class_a:
    """ Doc string for the module """
    def a_function(x, y):
        print(x)
        print(y)

@modulize('a.b.foo', dependencies=['a.b.foo'])
class dummy_class_foo:
    import a.b.bar as bar # mutually dependent modules

    foo_var = 'foo'

    def foo_func(x):
        return "{} is not {}".format(x, bar.bar_var)

@modulize('a.b.bar')
class the_name_of_this_class_does_not_matter:
    import a.b.foo as foo # mutually dependent modules

    bar_var = 'bar'

    def bar_func(x):
        return "{} is not {}".format(x, foo.foo_var)

    if __name__ == '__main__': # This will be skipped!
       print(bar_func(bar_var)) 

if __name__ == '__main__':
    from a import a_function, b
    from b.foo import foo_func
    from b.bar import bar_func

    a_function(foo_func('baz'), bar_func('baz')) # baz is not foo
                                                 # baz is not bar
```

Here are a few fine points:
- Modules should be added in the order of their dependencies.
- For the (rare) case of mutually dependent modules, one can pass a `dependencies` argument to `@modulize`. This is only needed when the module being added comes before the module it depends on.  (Also, a.b.foo doesn't need to add `a.b` as a dependency.  This is done automatically.)
- The code in the dummy class is run at the time the class is created, not at that time of import.  *Be careful, this may effect the desired behavior.*
- A module must be imported for it to be used.

### Code ###

```python 
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
```
- `@modulize` creates a `MockModule` object (inheriting from `types.ModuleType`) which passes all attribute calls to the underlying class.  
- This MockModule object is added to `sys.modules`.  It's name is not in the name space until it is imported.
- The `__name__` variable is changed during the class creation so that `if __name__ == '__main__':` conditions fail.
- If `a.b.c` is added as a module, then `a` and `a.b` are automatically added as well if they are not already in `sys.modules`.  Also `a` and `a.b` are marked as packages by setting their `__path__` attribute.

### Known issues ###
- Relative imports, e.g. `from . import foo` are not supported.
- Code inside the underlying class will be run at the time of creation, not the time of import.
- Nonstandard behavior might be observed if a variable has the same name as a submodule (for example. `a.b.foo = 5` as well as a module `a.b.foo`.)
- The `imp` and `importlib` modules have not been tested.
- This is ultimately a _**hack of the import system**_ and one should not hope for an exact replica.  Nonetheless, I tried to make it close!

-----
## <a name="combine"></a> `combine_py_files.py` script ##

### Usage: `python combine_py_files.py entry_point output_file`  ###

- **`entry_point`** is the file or directory to start (as if one was running `python entry_point`).  If it is a directory, it will start at the file `__main__.py` in that directory.
- **`output_file`** is the name of the combined Python file.

### Example ###

Directory structure and `.py` files:
```python
my_dir/
    __main__.py

        import foo.bar
        fb = foo.bar.bar_func(foo.foo_var)
        print(fb) # foo bar

    foo/
        __init__.py

            foo_var = 'foo'

        bar.py
    
            def bar_func(x):
                return x + ' bar'
```

Running the script:
```sh
$ python combine_py_files.py my_dir/ combined.py
... foo/__init__.py
... foo/bar.py
... __main__.py
Successfully combined files.
```

combined.py:
```python
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

@modulize('foo')
class _foo:
    ##----- Begin foo/__init__.py ------------------------------------------------##
    foo_var = 'foo'
    ##----- End foo/__init__.py --------------------------------------------------##
    pass

@modulize('foo.bar')
class _bar:
    ##----- Begin foo/bar.py -----------------------------------------------------##
    def bar_func(x):
        return x + ' bar'
    ##----- End foo/bar.py -------------------------------------------------------##
    pass


##----- Begin __main__.py ----------------------------------------------------##
import foo.bar
fb = foo.bar.bar_func(foo.foo_var)
print(fb) # foo bar
##----- End __main__.py ------------------------------------------------------##
```

### Notes ###
- This script has a very basic logic to find the module files and to determine the order to load them.  
  - First it looks for lines containing `import ...` or `from ... import`.  These statements must be on their own line (possibly indented).  The script ignores all of the surrounding code *including whether or not the `import` statement is inside an `if` block*.
  - Then it looks for the desired Python file and repeats the process.

  This usually works in practice, but their are no guarantees.
- All the modules are run at the beginning of the combined script, not during their import.  If the modules run code (and not just define functions and variables), then the behavior of the single combined Python script may be different from the original collection of scripts.


-----
## <a name="sync"></a> `sync_combined_py_files.py` script ##

**Still in progress**
