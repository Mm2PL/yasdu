import code
import sys

try:
    HAS_IPYTHON = False
    import IPython.terminal.embed
    from IPython.terminal.prompts import Prompts, Token

    HAS_IPYTHON = True


    class CustomPrompt(Prompts):
        def in_prompt_tokens(self):
            p = super().in_prompt_tokens()
            if self.note:
                p.insert(0, (Token.CustomPrompt, self.note))
            return p

        def __init__(self, note, shell):
            super().__init__(shell)
            self.note = note
except ImportError:
    pass  # CustomPrompt will not be used if IPython can't be imported


def spawn_shell(locals_, globals_, note=None) -> None:
    if HAS_IPYTHON:
        _spawn_ipython_shell(globals_, locals_, note)
    else:
        if note:
            sys.ps1 = note + ' >>> '
            sys.ps2 = note + ' ... '
        try:
            _spawn_code_shell(globals_, locals_)
        finally:
            sys.ps1 = '>>> '
            sys.ps2 = '... '


def _spawn_ipython_shell(globals_, locals_, note):
    print('Using IPython for shell...')
    print()
    namespace = Namespace()
    namespace.__dict__ = globals_
    shell = IPython.terminal.embed.InteractiveShellEmbed()
    shell.prompts = CustomPrompt(note, shell)
    shell(local_ns=locals_, module=namespace)


def _spawn_code_shell(globals_, locals_):
    print('Unable to use IPython for shell, trying built-in code console...')
    print()

    namespace = {}
    namespace.update(globals_)
    namespace.update(locals_)
    cons = code.InteractiveConsole(locals=namespace)
    cons.interact()


class Namespace:
    __dict__ = {}


__all__ = ['spawn_shell']
