"""Opt-in isolated-server diagnostics, never enabled for paired browser timing.

Transaction durations include SQLite work/fsync as well as lock waiting; they
are an upper bound, not a claim to isolate pure lock-wait time.
"""
import json
import resource
import sqlite3
import threading
import time
import platform


class Diagnostics:
    def __init__(self, output):
        self.output = output
        self.lock = threading.Lock()
        self.live = {}
        self.active = 0
        self.original_connect = sqlite3.connect
        self.stop = threading.Event()

    def emit(self, kind, **value):
        with self.lock:
            with self.output.open('a') as stream:
                stream.write(json.dumps({'at': time.time(), 'event': kind, **value})+'\n')

    def install(self):
        monitor = self

        class Connection(sqlite3.Connection):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.probe_path = str(args[0] if args else kwargs['database'])
                self.probe_id = id(self)
                with monitor.lock:
                    monitor.live[self.probe_id] = self.probe_path
                monitor.emit('connection_open', connection=self.probe_id, path=self.probe_path)

            def execute(self, sql, *args, **kwargs):
                action = sql.strip().split(' ', 1)[0].upper()
                if action not in ('BEGIN', 'COMMIT', 'ROLLBACK'):
                    return super().execute(sql, *args, **kwargs)
                start = time.perf_counter()
                error = None
                try:
                    return super().execute(sql, *args, **kwargs)
                except BaseException as exc:
                    error = type(exc).__name__
                    raise
                finally:
                    monitor.emit('transaction_statement', connection=self.probe_id,
                                 path=self.probe_path, action=sql, error=error,
                                 elapsed_ms=(time.perf_counter()-start)*1000)

            def __exit__(self, *args):
                start = time.perf_counter()
                try:
                    return super().__exit__(*args)
                finally:
                    monitor.emit('transaction_exit', connection=self.probe_id,
                                 path=self.probe_path, rollback=bool(args[0]),
                                 elapsed_ms=(time.perf_counter()-start)*1000)

            def close(self):
                try:
                    return super().close()
                finally:
                    with monitor.lock:
                        existed = monitor.live.pop(self.probe_id, None)
                    if existed is not None:
                        monitor.emit('connection_close', connection=self.probe_id, path=self.probe_path)

        def connect(*args, **kwargs):
            kwargs.setdefault('factory', Connection)
            return self.original_connect(*args, **kwargs)
        sqlite3.connect = connect

    def request(self, entering):
        with self.lock:
            self.active += 1 if entering else -1
            active = self.active
        self.emit('request_active', count=active)

    def start(self, server):
        def sample():
            while not self.stop.wait(.25):
                with self.lock:
                    live = list(self.live.values())
                    active = self.active
                usage = resource.getrusage(resource.RUSAGE_SELF)
                self.emit('resources', active=active, queued=server._requests.qsize(),
                          worker_threads=sum(t.is_alive() for t in server._workers),
                          connections=live, threads=threading.active_count(),
                          peak_rss_bytes=usage.ru_maxrss*(1 if platform.system()=='Darwin' else 1024))
        self.thread = threading.Thread(target=sample, name='performance-diagnostic')
        self.thread.start()

    def close(self):
        self.stop.set()
        if hasattr(self, 'thread'):
            self.thread.join()
        sqlite3.connect = self.original_connect
        with self.lock:
            remaining = dict(self.live)
        self.emit('stopped', remaining_connections=remaining)
