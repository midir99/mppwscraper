import logging
from functools import partial

import ws.mor.amber
import ws.mor.custom
import ws.mpp

MAX_RECORDS = 15
WSCRAPPERS = [
    (
        "mx_mor_amber",
        partial(
            ws.mor.amber.run_ws,
            wsid="mx_mor_amber",
        ),
    ),
    (
        "mx_mor_custom",
        partial(ws.mor.custom.run_ws, wsid="mx_mor_custom", max_records=MAX_RECORDS),
    ),
]


def webscrap_mpps() -> list[ws.mpp.MissingPersonPoster]:
    for wsid, ws in WSCRAPPERS:
        logging.info("Starting web scrapper %s", wsid)
        try:
            mpp_list = ws()
        except Exception as e:
            logging.exception(
                "Ending web scrapper %s, an exception occurred while scrapping",
                wsid,
            )
            mpp_list = []
        else:
            logging.info(
                "Ending web scrapper %s, %s MPPs were retrieved",
                wsid,
                len(mpp_list),
            )

        yield wsid, mpp_list
