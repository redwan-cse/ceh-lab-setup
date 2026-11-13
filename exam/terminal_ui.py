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


def install_chat_history_renderer(session_class):
    """Render saved tool-only messages without changing API history on disk.

    ShellGPT 1.5.1 indexes every message's content while validating/displaying
    a saved chat. Assistant tool calls may legitimately omit content or use
    null. Keep that metadata intact for requests; format only the display copy.
    """
    def get_messages(self,chat_id):
        rendered=[]
        for message in self._read(chat_id):
            role=message['role']
            content=message.get('content')
            if content is None:
                names=[]
                for call in message.get('tool_calls') or []:
                    name=call.get('function',{}).get('name','unknown')
                    names.append(str(name))
                content='[Tool calls: '+', '.join(names)+']' if names else '[No text]'
            rendered.append(f'{role}: {content}')
        return rendered
    session_class.get_messages=get_messages
