"""Keep tool output and interactive approvals in a stable terminal transcript."""
import sys


class ApprovalRefusal(str):
    """Typed outcome; untrusted command output cannot impersonate a refusal."""


class ApprovalDeclined(RuntimeError):
    """Stop this task's tool loop while leaving an interactive chat available."""


def interactive_input(prompt,interactive=None):
    # ShellGPT can reopen CON or /dev/tty after reading piped input. Use the
    # entry-point state when supplied, rather than trusting a reopened console.
    allowed=sys.stdin.isatty() if interactive is None else interactive
    if not allowed:raise EOFError('Approval requires an interactive terminal')
    return input(prompt)


class TerminalPrinter:
    """ShellGPT printer protocol without Rich Live or spinner redirection.

    ShellGPT advances its completion generator inside the renderer. That generator
    also executes tools and asks for approval, so neither streaming mode may keep
    a live renderer active while it advances. Emit each chunk once and flush it
    before the next tool can read input, including with --no-stream.
    """

    def __call__(self, chunks, live=True):
        completion = []
        for chunk in chunks:
            completion.append(chunk)
            sys.stdout.write(chunk)
            sys.stdout.flush()
        text = ''.join(completion)
        if text and not text.endswith('\n'):
            sys.stdout.write('\n')
            sys.stdout.flush()
        return text


def install_terminal_printer(handler_class):
    """Replace only the exam process's ShellGPT renderer, leaving guards intact."""
    handler_class.printer = property(lambda self: TerminalPrinter())
