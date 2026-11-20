"""Keep tool output and interactive approvals in a stable terminal transcript."""
import hashlib
import os
from pathlib import Path
import sys

from file_locking import FileLockBusy, file_lock


class ApprovalRefusal(str):
    """Typed outcome; untrusted command output cannot impersonate a refusal."""


class ApprovalDeclined(RuntimeError):
    """Stop this task's tool loop while leaving an interactive chat available."""


class ChatAlreadyOpen(RuntimeError):
    """A named chat already has a live CLI writer."""


def install_chat_writer_guard(handler_class, get_context):
    """Own the chat before its first read and release it on CLI exit."""
    if handler_class.__dict__.get('_ceh_chat_writer_guard'):
        return
    original_init = handler_class.__init__

    def init(self, chat_id, *args, **kwargs):
        context = get_context(silent=True)
        self._ceh_chat_id = chat_id
        if context is not None and chat_id:
            storage = Path(self.chat_session.storage_path)
            cache_path = os.path.normcase(str((storage / chat_id).resolve()))
            digest = hashlib.sha256(os.fsencode(cache_path)).hexdigest()
            lock_dir = storage.parent.parent / 'chat-locks'
            lock_dir.mkdir(mode=0o700, exist_ok=True)
            if lock_dir.is_symlink() or getattr(lock_dir, 'is_junction', lambda: False)():
                raise RuntimeError('Redirected chat lock directory refused')
            try:
                context.with_resource(file_lock(lock_dir / (digest + '.lock'), blocking=False))
            except FileLockBusy:
                raise ChatAlreadyOpen('This chat is open in another terminal. Use a different --repl or --chat name, or close the other session.') from None
        original_init(self, chat_id, *args, **kwargs)

    handler_class.__init__ = init
    handler_class._ceh_chat_writer_guard = True


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


def _whole_chat_turns(messages,limit=None):
    """Keep the role plus complete user turns, never a sliced tool exchange."""
    if not messages:return []
    users=[index for index,message in enumerate(messages) if index and message.get('role')=='user']
    if not users:return messages[:1]
    start=users[0]
    if limit is not None and len(messages)>limit:
        threshold=max(1,len(messages)-max(2,limit)+1)
        candidates=[index for index in users if index>=threshold]
        # A single long current turn is kept whole even beyond the target size.
        start=candidates[0] if candidates else users[-1]
    return messages[:1]+messages[start:]


def install_chat_cache_guard(session_class):
    """Preserve complete tool history when upstream's message cache fills."""
    if session_class.__dict__.get('_ceh_complete_turn_cache'):return
    original_read=session_class._read;original_write=session_class._write
    def read(self,chat_id):
        # Old upstream truncation may already have cut off the leading user and
        # assistant call. Normalize the request/display copy, not the disk file.
        return _whole_chat_turns(original_read(self,chat_id))
    def write(self,messages,chat_id):
        target=self.length
        retained=_whole_chat_turns(messages,max(2,int(target)))
        # Keep upstream serialization/storage behavior, but prevent it from
        # slicing a retained long turn for a second time.
        self.length=max(int(target),len(retained))
        try:return original_write(self,retained,chat_id)
        finally:self.length=target
    session_class._read=read;session_class._write=write
    session_class._ceh_complete_turn_cache=True
