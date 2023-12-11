from RestrictedPython import compile_restricted, safe_builtins
from config import Config
import multiprocessing
import timeout_decorator

class AnimationProcess(multiprocessing.Process):
    def __init__(self, pixels, filepath, result_queue):
        super().__init__()
        self.pixels = pixels
        self.filepath = filepath
        self.result_queue = result_queue

    def run(self):
        try:
            execute_animation_bytecode(self.pixels, self.filepath)
        except timeout_decorator.timeout_decorator.TimeoutError:
            self.result_queue.put('TimeoutError')
        except KeyboardInterrupt:
            self.result_queue.put('KeyboardInterrupt')
        except Exception as e:
            self.result_queue.put(str(e))
        else:
            self.result_queue.put('Success')

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

@timeout_decorator.timeout(Config.ANIMATION_RUN_TIME, use_signals=False)
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

@timeout_decorator.timeout(Config.TEST_RUN_TIME, use_signals=False)
def execute_test_bytecode(byte_code, pixels):
    restricted_globals = {
        '__builtins__': {
            **safe_builtins,
            '__import__': _safe_import
        },
        "_getiter_": iter,
        "_write_": _write_,
        '_inplacevar_': protected_inplacevar
    }
    try:
        exec(byte_code, restricted_globals)
        restricted_globals['animation'](pixels)
    except:
        raise