from RestrictedPython import compile_restricted, safe_builtins
import sys
import timeout_decorator

ANIMATION_TIMEOUT = 180
NUMBER_OF_PIXELS = 200

_SAFE_MODULES = frozenset(('math', 'time', 'random',))

def _safe_import(name, *args, **kwargs):
    if name not in _SAFE_MODULES:
        raise Exception(f"Module {name!r} is restricted.")
    return __import__(name, *args, **kwargs)

def _write_(object):
    if hasattr(object, '_guarded_writes'):
        return object
    raise Exception(f'Object not writable!')

valid_inplace_types = (list, set)

inplace_slots = {
    '+=': '__iadd__',
    '-=': '__isub__',
    '*=': '__imul__',
    '/=': (1 / 2 == 0) and '__idiv__' or '__itruediv__',
    '//=': '__ifloordiv__',
    '%=': '__imod__',
    '**=': '__ipow__',
    '<<=': '__ilshift__',
    '>>=': '__irshift__',
    '&=': '__iand__',
    '^=': '__ixor__',
    '|=': '__ior__',
}

def __iadd__(x, y):
    x += y
    return x

def __isub__(x, y):
    x -= y
    return x

def __imul__(x, y):
    x *= y
    return x

def __idiv__(x, y):
    x /= y
    return x

def __ifloordiv__(x, y):
    x //= y
    return x

def __imod__(x, y):
    x %= y
    return x

def __ipow__(x, y):
    x **= y
    return x

def __ilshift__(x, y):
    x <<= y
    return x

def __irshift__(x, y):
    x >>= y
    return x

def __iand__(x, y):
    x &= y
    return x

def __ixor__(x, y):
    x ^= y
    return x

def __ior__(x, y):
    x |= y
    return x

inplace_ops = {
    '+=': __iadd__,
    '-=': __isub__,
    '*=': __imul__,
    '/=': __idiv__,
    '//=': __ifloordiv__,
    '%=': __imod__,
    '**=': __ipow__,
    '<<=': __ilshift__,
    '>>=': __irshift__,
    '&=': __iand__,
    '^=': __ixor__,
    '|=': __ior__,
}

def protected_inplacevar(op, var, expr):
    """Do an inplace operation
    If the var has an inplace slot, then disallow the operation
    unless the var an instance of ``valid_inplace_types``.
    """
    if hasattr(var, inplace_slots[op]) and \
       not isinstance(var, valid_inplace_types):
        try:
            cls = var.__class__
        except AttributeError:
            cls = type(var)
        raise TypeError(
            "Augmented assignment to %s objects is not allowed"
            " in untrusted code" % cls.__name__)
    return inplace_ops[op](var, expr)

def load_and_test_animation(filepath):
    try:
        with open(filepath, 'r', encoding='latin-1') as fd:
            user_code = fd.read()
    except:
        raise
    try:
        byte_code = compile_restricted(user_code, filename='<user_code>', mode='exec')
    except SyntaxError:
        raise
    return byte_code

@timeout_decorator.timeout(ANIMATION_TIMEOUT, use_signals=False)
def execute_animation_bytecode(pixels, filepath):
    byte_code = load_and_test_animation(filepath)
    restricted_globals = {
        '__builtins__': {
            **safe_builtins,
            '__import__': _safe_import
        },
        '_getiter_': iter,
        '_write_': _write_,
        '_inplacevar_': protected_inplacevar
    }
    exec(byte_code, restricted_globals)
    restricted_globals['animation'](pixels)

# For testing purposes we use this dummy class
# instead of the real NeoPixel one
# Functionality is the same
class DummyNeoPixel(object):
    _guarded_writes = True
    def __init__(self, n, debug):
        self.n = n
        self.debug = debug
    def show(self):
        if self.debug: print('pixels.show()')
    def fill(self, color):
        if self.debug: print(f'pixels.fill({color})')
    def __setitem__(self, key, value):
        if self.debug: print(f'pixels[{key}] = {value}')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f'Usage: {sys.argv[0]} <animation file>')
        sys.exit(1)

    # Set debug to true to debug your program
    pixels = DummyNeoPixel(NUMBER_OF_PIXELS, True)
    try:
        execute_animation_bytecode(pixels, sys.argv[1])
    except timeout_decorator.timeout_decorator.TimeoutError:
        print(f'Your code successfully ran for {ANIMATION_TIMEOUT} seconds!')
    except KeyboardInterrupt:
        print('Aborted.')
    except Exception as e:
        import traceback
        print(traceback.print_exc())
    else:
        print('Your code executed without issues!')
