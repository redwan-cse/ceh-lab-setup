"""Short cross-process locks for local evidence and script metadata."""
from contextlib import contextmanager
import os
from pathlib import Path


@contextmanager
def file_lock(path):
    path=Path(path)
    if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('Redirected lock refused')
    with path.open('a+b') as stream:
        stream.seek(0,2)
        if not stream.tell():stream.write(b'\0');stream.flush()
        stream.seek(0)
        if os.name=='nt':
            import msvcrt
            msvcrt.locking(stream.fileno(),msvcrt.LK_LOCK,1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX)
        try:yield
        finally:
            stream.seek(0)
            if os.name=='nt':msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)
