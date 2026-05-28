"""DataUpdateCoordinator for East Suffolk Bins."""
from __future__ import annotations

import http.cookiejar
import json
import urllib.request
from datetime import date, datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_DAYS, DOMAIN, UPDATE_INTERVAL

_BASE = "https://my.eastsuffolk.gov.uk"
_APIBROKER = _BASE + "/apibroker/runLookup"
_IFRAME_URL = _BASE + "/fillform/?iframe_id=fillform-frame-1&db_id="
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ha-east-suffolk-bins)",
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": _IFRAME_URL,
}


def _fetch_raw(uprn: str, days: int) -> list[dict]:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    for url in (_BASE + "/service/Bin_collection_dates_finder", _IFRAME_URL):
        req = urllib.request.Request(url, headers={"User-Agent": _HEADERS["User-Agent"]})
        with opener.open(req) as resp:
            resp.read()

    sid = next((c.value for c in jar if c.name == "PHPSESSID"), "")

    def _post(lookup_id: str, body: bytes, extra_params: str = "") -> dict:
        ts = int(datetime.now().timestamp() * 1000)
        url = (
            f"{_APIBROKER}?id={lookup_id}&repeat_against=&noRetry=false"
            f"&getOnlyTokens=undefined&log_id=&app_name=AF-Renderer::Self"
            f"&_={ts}&sid={sid}{extra_params}"
        )
        req = urllib.request.Request(url, data=body, headers=_HEADERS)
        with opener.open(req) as resp:
            raw = resp.read().decode("utf-8")
        return json.JSONDecoder(strict=False).decode(raw)

    auth_payload = _post("59e73f8bd860c", b"{}", extra_params="&noRetry=true")
    auth_token = (
        auth_payload
        .get("integration", {})
        .get("transformed", {})
        .get("rows_data", {})
        .get("0", {})
        .get("AuthenticateResponse", "")
    )
    if not auth_token:
        raise RuntimeError("Empty Bartec auth token — session may not have initialised")

    today = date.today()
    end = today + timedelta(days=days)
    body = json.dumps({
        "formValues": {
            "Details": {
                "AuthenticateResponse": {"value": auth_token},
                "finalUPRN":            {"value": uprn},
                "minimum_date":         {"value": today.strftime("%Y-%m-%dT00:00:00")},
                "maximum_date":         {"value": end.strftime("%Y-%m-%dT00:00:00")},
            }
        }
    }).encode()

    bins_payload = _post("68f900a32e7a4", body)
    rows_data = (
        bins_payload
        .get("integration", {})
        .get("transformed", {})
        .get("rows_data", {})
    )

    if not rows_data:
        return []

    return [rows_data[k] for k in sorted(rows_data, key=lambda x: int(x))]


def _parse_date(iso_datetime: str) -> date | None:
    try:
        return datetime.strptime(iso_datetime[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _parse_rows(raw_rows: list[dict], days: int) -> list[dict]:
    today = date.today()
    cutoff = today + timedelta(days=days)
    result = []

    for row in raw_rows:
        d = _parse_date(row.get("CollectionDate", ""))
        if d is None or d < today or d > cutoff:
            continue

        descriptive = row.get("CollectionTypeDescriptive", "").strip()

        if " - " in descriptive:
            parts = descriptive.split(" - ", 1)
            label_part = parts[0].strip()
            container = parts[1].strip()
        else:
            label_part = descriptive
            container = ""

        words = label_part.split()
        if words:
            first = words[0]
            if any(ord(c) > 127 for c in first):
                emoji = first
                bin_type = " ".join(words[1:])
            else:
                emoji = "🗑️"
                bin_type = label_part
        else:
            emoji = "🗑️"
            bin_type = descriptive

        result.append({
            "date": d.isoformat(),
            "date_label": d.strftime("%a %d/%m/%Y"),
            "bin_type": bin_type,
            "container": container,
            "emoji": emoji,
            "label": f"{emoji} {bin_type}",
        })

    return sorted(result, key=lambda x: x["date"])


class BinCollectionCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, uprn: str) -> None:
        super().__init__(
            hass,
            logger=__import__("logging").getLogger(__name__),
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.uprn = uprn
        self.collections: list[dict] = []
        self.today: str = ""
        self.tomorrow: str = ""
        self.error: str | None = None

    async def _async_update_data(self) -> dict:
        today = date.today()
        self.today = today.isoformat()
        self.tomorrow = (today + timedelta(days=1)).isoformat()
        try:
            raw = await self.hass.async_add_executor_job(
                _fetch_raw, self.uprn, DEFAULT_DAYS
            )
            self.collections = _parse_rows(raw, DEFAULT_DAYS)
            self.error = None
        except Exception as exc:
            self.error = str(exc)
            self.collections = []
            raise UpdateFailed(str(exc)) from exc

        return {
            "collections": self.collections,
            "today": self.today,
            "tomorrow": self.tomorrow,
            "error": self.error,
        }
