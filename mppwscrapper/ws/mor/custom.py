import datetime
import logging
import urllib.error
import urllib.request
from typing import Any

import bs4

from .. import dbutils, mpp

BASE_URL = "https://fiscaliamorelos.gob.mx/cedulas"
SPANISH_MONTHS_MAP = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


def make_url(page_number: int) -> str:
    return f"{BASE_URL}/{page_number}/"


def parsedate(datestr: str) -> datetime.date:
    datestr = datestr.strip()
    try:
        month, day, year = map(lambda s: s.strip(), datestr.split(" "))
    except ValueError as e:
        raise ValueError(f'Unable to parse the date "{datestr}"') from e

    try:
        month = SPANISH_MONTHS_MAP[month]
    except KeyError as e:
        raise ValueError(f'Unable to parse the date "{datestr}"') from e

    try:
        day = int(day[:-1])
    except ValueError as e:
        raise ValueError(f'Unable to parse the date "{datestr}"') from e

    try:
        year = int(year)
    except ValueError as e:
        raise ValueError(f'Unable to parse the date "{datestr}"') from e

    try:
        return datetime.date(year, month, day)
    except ValueError as e:
        raise ValueError(f'Unable to parse the date "{datestr}"') from e


def scrap_mpp_data(article) -> dict[str, Any]:
    mpp_data = {}
    try:
        mpp_data["mp_name"] = article.h3.a.get_text().strip().title()
    except AttributeError as e:
        logging.exception("Unable to get the mp_name from the article: %s", article)
        raise e

    try:
        mpp_data["po_post_url"] = article.h3.a.get("href", "").strip()
    except AttributeError as e:
        logging.exception("Unable to get the po_post_url from the article: %s", article)
        raise e

    try:
        datestr = article.span.get_text().strip()
        mpp_data["po_post_publication_date"] = parsedate(datestr)
    except (AttributeError, ValueError) as e:
        logging.exception(
            "Unable to get the po_post_publication_date from the article: %s",
            article,
        )
        mpp_data["po_post_publication_date"] = ""

    try:
        mpp_data["po_poster_url"] = article.img.get("src", "").strip()
        mpp_data["po_poster_url"] = mpp_data["po_poster_url"].replace("-300x225", "")
    except AttributeError as e:
        logging.exception(
            "Unable to get the po_poster_url from the article: %s",
            article,
        )
        mpp_data["po_poster_url"] = ""

    return mpp_data


def scrap_mpps_from_soup(
    soup: bs4.BeautifulSoup,
    last_po_post_url_visited: str,
) -> tuple[list[mpp.MissingPersonPoster], bool]:
    articles = soup.find_all("article")
    mpps = []
    must_stop = False
    for article in articles:
        try:
            m = mpp.MissingPersonPoster(**scrap_mpp_data(article))
        except AttributeError as e:
            logging.exception(
                "Cannot add a MissingPersonPoster without name or po_post_url, skipping"
            )
        else:
            mpps.append(m)
            if m.po_post_url == last_po_post_url_visited:
                must_stop = True
                break

    return (mpps, must_stop)


def scrap_mpps(
    last_po_post_url_visited="", max_records=30
) -> list[mpp.MissingPersonPoster]:
    page = 1
    mpps = []
    while True:
        url = make_url(page)
        req = urllib.request.Request(url)
        try:
            with urllib.request.urlopen(req) as response:
                page_html = response.read().decode("UTF-8")
            soup = bs4.BeautifulSoup(page_html, "html.parser")
            mpp_list, must_stop = scrap_mpps_from_soup(soup, last_po_post_url_visited)
            mpps += mpp_list
            logging.info("%s MPPs were scrapped from %s", len(mpp_list), url)
            if must_stop:
                break
            mpp_scrapped_count = len(mpps)
            if mpp_scrapped_count > max_records:
                logging.info(
                    "Max ammount of records has been reached (%s)",
                    mpp_scrapped_count,
                )
                mpps = mpps[:max_records]
                break
            page += 1
        except urllib.error.HTTPError as e:
            logging.warn("Unable to scrap more MPPs from %s", url)
            break

    return mpps


def add_common_data_to_mpp(mpp_: mpp.MissingPersonPoster):
    mpp_.alert_type = mpp.AlertTypeChoices.OTHER.value
    mpp_.po_state = mpp.StateChoices.MORELOS.value
    return mpp_


def run_ws(wsid: str, max_records: int) -> list[mpp.MissingPersonPoster]:
    lppuv = dbutils.get_last_po_post_url_visited_by_id(wsid)
    logging.info("Scrapping until URL %s is found", lppuv)
    mpps = scrap_mpps(lppuv, max_records)
    mpps = list(map(add_common_data_to_mpp, mpps))
    last_po_post_url = mpps[0].po_post_url if mpps else ""
    logging.info(
        "Updating wscrapper %s in the database with the first URL scrapped (%s)",
        wsid,
        last_po_post_url,
    )
    dbutils.set_last_po_post_url_visited_by_id(wsid, last_po_post_url)
    return mpps
