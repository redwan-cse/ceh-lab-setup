"""Cross-process locks for local evidence, scripts, and chat writers."""
from contextlib import contextmanager
import errno
import os
from pathlib import Path


class FileLockBusy(RuntimeError):
    """A nonblocking lock is held by another writer."""


@contextmanager
def file_lock(path, *, blocking=True):
    path=Path(path)
    if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('Redirected lock refused')
    with path.open('a+b') as stream:
        stream.seek(0,2)
        if not stream.tell():stream.write(b'\0');stream.flush()
        stream.seek(0)
        try:
            if os.name=='nt':
                import msvcrt
                mode = msvcrt.LK_LOCK if blocking else msvcrt.LK_NBLCK
                msvcrt.locking(stream.fileno(),mode,1)
            else:
                import fcntl
                mode = fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB
                fcntl.flock(stream.fileno(),mode)
        except OSError as error:
            if not blocking and error.errno in (errno.EACCES, errno.EAGAIN):
                raise FileLockBusy() from error
            raise
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)
