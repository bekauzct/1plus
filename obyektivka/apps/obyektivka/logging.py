"""Log filtri: request body, POST ma'lumotlari va so'rov obyekti log'larga tushmaydi.

django.request logger xatolarda ``record.request`` ni biriktiradi; formatter yoki
tashqi handler (Sentry va h.k.) undan body'ni o'qishi mumkin. Shu sababli uni olib tashlaymiz.
"""

import logging


class NoBodyFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        req = getattr(record, "request", None)
        if req is not None:
            method = getattr(req, "method", "?")
            path = getattr(req, "path", "?")
            record.request = f"<{method} {path}>"
        return True
