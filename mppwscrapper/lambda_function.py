import logging

from config import settings
from missingsapi.utils import count_mpps_by_post_url, create_mpp
from ws import runner

# def lambda_handler(event, context):
#     # TODO implement
#     return {
#         'statusCode': 200,
#         'body': json.dumps('Hello from Lambda!')
#     }


def setup_logging():
    logging.basicConfig(
        level=settings["LOGGING"]["level"],
        encoding="UTF-8",
        format="%(asctime)s:%(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %I:%M:%S %p",
    )


def lambda_handler(event, context):
    setup_logging()
    logging.info("Lambda execution has started")
    for wsid, mpp_list in runner.webscrap_mpps():
        logging.info("Saving MPPs scrapped by %s", wsid)
        for mpp in mpp_list:
            if exists := count_mpps_by_post_url(mpp.po_post_url):
                logging.info(
                    "%s won't be created because it already exists (%s)",
                    mpp.mp_name,
                    exists,
                )
            else:
                logging.info("Creating %s", mpp.mp_name)
                create_mpp(mpp, settings["MISSINGS_API"]["token"])

    logging.info("Lambda execution terminated")


if __name__ == "__main__":
    lambda_handler(None, None)
