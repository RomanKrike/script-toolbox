# -*- coding: utf-8 -*-
from __future__ import print_function

import datetime
import json
import threading
import uuid

try:
    import Queue as queue
except ImportError:
    import queue

try:
    from urllib2 import Request
    from urllib2 import urlopen
except ImportError:
    from urllib.request import Request
    from urllib.request import urlopen

from ..constants import PLUGIN_VERSION
from ..pycompat import text_type
from .provider import TelemetryProvider
from .provider import TelemetryProviderError


POSTHOG_BATCH_PATH = "/batch/"
USER_AGENT = (
    "Script-Toolbox-Telemetry/{0} "
    "(github.com/RomanKrike/script-toolbox)"
).format(PLUGIN_VERSION)


class PostHogProvider(TelemetryProvider):
    """Small dependency-free PostHog event provider.

    Events are queued onto a daemon worker so analytics can never block the DCC
    UI. The distinct id is random and process-scoped; it is not persisted and
    is not derived from hardware, usernames, hostnames, or project data.
    """

    name = "posthog"

    def __init__(
        self,
        project_token,
        host,
        timeout=3,
        max_queue_size=256,
        distinct_id=None
    ):
        self.project_token = text_type(
            project_token or ""
        ).strip()
        self.host = text_type(
            host or ""
        ).strip().rstrip("/")
        self.timeout = max(1, int(timeout))
        self.distinct_id = text_type(
            distinct_id or (
                "stb-session-{0}".format(
                    uuid.uuid4().hex
                )
            )
        )

        if not self.project_token:
            raise TelemetryProviderError(
                "PostHog project token is missing."
            )
        if not self.host:
            raise TelemetryProviderError(
                "PostHog host is missing."
            )

        self._queue = queue.Queue(
            maxsize=max(1, int(max_queue_size))
        )
        self._worker = None
        self._worker_lock = threading.Lock()
        self._closed = False

    @property
    def endpoint(self):
        return self.host + POSTHOG_BATCH_PATH

    def capture(self, event_name, properties=None):
        if self._closed:
            return False

        event_name = text_type(
            event_name or ""
        ).strip()
        if not event_name:
            return False

        payload_properties = dict(
            properties or {}
        )

        # Provider-owned keys cannot be overridden by feature instrumentation.
        # Anonymous events deliberately do not create PostHog person profiles.
        payload_properties["distinct_id"] = self.distinct_id
        payload_properties["$process_person_profile"] = False
        payload_properties["$lib"] = "script-toolbox"
        payload_properties["$lib_version"] = PLUGIN_VERSION

        event = {
            "event": event_name,
            "properties": payload_properties,
        }

        self._ensure_worker()

        try:
            self._queue.put_nowait(event)
            return True
        except queue.Full:
            return False

    def flush(self):
        if self._worker is None:
            return True
        self._queue.join()
        return True

    def close(self):
        with self._worker_lock:
            if self._closed:
                return True
            self._closed = True
            worker = self._worker

        if worker is None:
            return True

        try:
            self._queue.put_nowait(None)
        except queue.Full:
            try:
                self._queue.put(None, True, self.timeout)
            except Exception:
                return False

        return True

    def _ensure_worker(self):
        if self._worker is not None:
            return

        with self._worker_lock:
            if self._worker is not None or self._closed:
                return

            worker = threading.Thread(
                target=self._worker_main,
                name="ScriptToolboxTelemetry"
            )
            worker.daemon = True
            self._worker = worker
            worker.start()

    def _worker_main(self):
        while True:
            event = self._queue.get()
            try:
                if event is None:
                    return
                try:
                    self._send_event(event)
                except Exception:
                    # Analytics is best-effort. Transport failures must never
                    # escape the background worker or affect Script Toolbox.
                    pass
            finally:
                self._queue.task_done()

    def _send_event(self, event):
        body = {
            "api_key": self.project_token,
            "sent_at": datetime.datetime.utcnow().isoformat() + "Z",
            "batch": [event],
        }

        data = json.dumps(
            body,
            ensure_ascii=False,
            separators=(",", ":")
        )
        if not isinstance(data, bytes):
            data = data.encode("utf-8")

        request = Request(
            self.endpoint,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": USER_AGENT,
            }
        )

        response = None
        try:
            response = urlopen(
                request,
                timeout=self.timeout
            )
            status = getattr(
                response,
                "getcode",
                lambda: 200
            )()
            if status is not None and not (200 <= int(status) < 300):
                raise TelemetryProviderError(
                    "PostHog returned HTTP {0}.".format(status)
                )
        except TelemetryProviderError:
            raise
        except Exception as exc:
            raise TelemetryProviderError(
                "Could not deliver PostHog event: {0}".format(
                    text_type(exc)
                )
            )
        finally:
            if response is not None:
                try:
                    response.close()
                except Exception:
                    pass

        return True


__all__ = [
    "POSTHOG_BATCH_PATH",
    "PostHogProvider",
]
