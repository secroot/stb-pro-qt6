"""
Reaktiver Qt6 Event-Bus & Asynchroner QThreadPool-Worker.
Ersetzt das langsame Tkinter after()-Polling durch echte Qt Signals & Slots.
"""
import traceback
from typing import Callable, Any, Optional
from PySide6.QtCore import QObject, Signal, QRunnable, QThreadPool, Slot


class AppEventBus(QObject):
    """Zentraler Signal-Bus für die gesamte Applikation."""
    log_message = Signal(str)                       # (text)
    http_Exchange_logged = Signal(object)           # (HttpLogEntry)
    connection_state_changed = Signal(bool, bool, str)  # (connected, loading, status_text)
    profile_updated = Signal(object)                # (Profile)
    channels_loaded = Signal(list, list)            # (List[Channel], List[str])
    vod_categories_loaded = Signal(list)            # (List[str])
    channel_selected = Signal(object)               # (Channel)
    channel_play_requested = Signal(object)         # (Channel)
    favorites_changed = Signal()
    recorder_changed = Signal()
    telemetry_updated = Signal(dict)                # (telemetry_dict)
    scan_result_received = Signal(dict)             # (result_dict)
    scan_progress_updated = Signal(int, int)        # (done, total)
    scan_state_changed = Signal(bool)               # (is_running)


class _WorkerSignals(QObject):
    finished = Signal(object)
    error = Signal(Exception, str)


class _AsyncTask(QRunnable):
    """Kapselt eine beliebige Funktion für den globalen QThreadPool."""
    def __init__(
        self,
        fn: Callable[..., Any],
        *args,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs,
    ):
        super().__init__()
        self.setAutoDelete(True)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = _WorkerSignals()
        if on_success:
            self.signals.finished.connect(on_success)
        if on_error:
            self.signals.error.connect(lambda exc, _tb: on_error(exc))

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as exc:
            tb = traceback.format_exc()
            self.signals.error.emit(exc, tb)


class AsyncWorkerPool(QObject):
    """
    Hochperformanter Thread-Pool auf Basis von Qt QThreadPool.
    Liefert Ergebnisse garantiert im Main-UI-Thread via Signals ab.
    """
    ui_dispatch_signal = Signal(object, tuple, dict)

    def __init__(self, max_workers: int = 16):
        super().__init__()
        self.pool = QThreadPool()
        self.pool.setMaxThreadCount(max_workers)
        self.ui_dispatch_signal.connect(self._execute_on_ui)
        self._active_tasks = set()

    @Slot(object, tuple, dict)
    def _execute_on_ui(self, fn: Callable, args: tuple, kwargs: dict):
        try:
            fn(*args, **kwargs)
        except Exception:
            pass

    def run_async(
        self,
        task_fn: Callable[..., Any],
        *args,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        **kwargs,
    ):
        task = _AsyncTask(task_fn, *args, on_success=on_success, on_error=on_error, **kwargs)
        # Referenz halten bis Task fertig ist, damit Python GC Signal-Objekte nicht vorzeitig abräumt
        self._active_tasks.add(task)
        task.signals.finished.connect(lambda _r, t=task: self._active_tasks.discard(t))
        task.signals.error.connect(lambda _e, _tb, t=task: self._active_tasks.discard(t))
        self.pool.start(task)
        return task

    def submit(self, fn: Callable[..., Any], *args, **kwargs):
        return self.run_async(fn, *args, **kwargs)

    def dispatch_to_ui(self, fn: Callable[..., Any], *args, **kwargs):
        self.ui_dispatch_signal.emit(fn, args, kwargs)

    def shutdown(self):
        self.pool.clear()
        self.pool.waitForDone(1500)


# Singleton-Instanzen
event_bus = AppEventBus()
worker_pool = AsyncWorkerPool(max_workers=18)
