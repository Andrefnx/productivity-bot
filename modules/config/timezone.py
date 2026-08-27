import asyncio
import time

from zoneinfo import available_timezones

import aiohttp


# -------------------------------------------------------
#                  TIMEZONE PROVIDER
# -------------------------------------------------------

TIMEZONE_API_URL = (
    "https://www.timeapi.io/api/timezone/availabletimezones"
)
TIMEZONE_CACHE_SECONDS = 24 * 60 * 60

_timezone_cache = None
_timezone_cache_time = 0
_timezone_cache_lock = asyncio.Lock()


def _normalize_timezones(data):
    if isinstance(data, list):
        values = data
    elif isinstance(data, dict):
        values = data.get(
            "timezones",
            data.get("data", [])
        )
    else:
        values = []

    return sorted({
        value.strip()
        for value in values
        if isinstance(value, str)
        and value.strip()
    })


def _zoneinfo_timezones():
    return sorted(
        available_timezones()
    )


def get_cached_timezones():
    if _timezone_cache:
        return list(
            _timezone_cache
        )

    return _zoneinfo_timezones()


async def get_available_timezones():
    global _timezone_cache
    global _timezone_cache_time

    now = time.monotonic()
    if (
        _timezone_cache
        and now - _timezone_cache_time < TIMEZONE_CACHE_SECONDS
    ):
        return list(_timezone_cache)

    async with _timezone_cache_lock:
        now = time.monotonic()
        if (
            _timezone_cache
            and now - _timezone_cache_time < TIMEZONE_CACHE_SECONDS
        ):
            return list(_timezone_cache)

        try:
            timeout = aiohttp.ClientTimeout(
                total=10
            )
            async with aiohttp.ClientSession(
                timeout=timeout
            ) as session:
                async with session.get(
                    TIMEZONE_API_URL
                ) as response:
                    response.raise_for_status()
                    data = await response.json()

            timezones = _normalize_timezones(
                data
            )
            if not timezones:
                raise ValueError(
                    "Timezone API returned no IANA zones."
                )

            _timezone_cache = timezones
            _timezone_cache_time = time.monotonic()

        except (
            aiohttp.ClientError,
            asyncio.TimeoutError,
            ValueError,
            TypeError,
            OSError
        ):
            return get_cached_timezones()

    return list(_timezone_cache)


# -------------------------------------------------------
#                  TIMEZONE SEARCH
# -------------------------------------------------------

async def search_timezones(
    search: str,
    limit: int = 25
):
    normalized_search = (
        (search or "")
        .strip()
        .lower()
        .replace(" ", "_")
    )

    if not normalized_search:
        return []

    timezones = await get_available_timezones()
    exact_matches = []
    city_matches = []
    prefix_matches = []
    partial_matches = []

    for timezone in timezones:
        lowered_timezone = timezone.lower()
        city = timezone.split("/")[-1].lower()

        if lowered_timezone == normalized_search:
            exact_matches.append(timezone)
        elif city == normalized_search:
            city_matches.append(timezone)
        elif city.startswith(normalized_search):
            prefix_matches.append(timezone)
        elif normalized_search in lowered_timezone:
            partial_matches.append(timezone)

    return (
        exact_matches
        + city_matches
        + prefix_matches
        + partial_matches
    )[:limit]


async def validate_timezone(
    timezone: str
):
    timezones = await get_available_timezones()
    matches = {
        value.lower(): value
        for value in timezones
    }

    return matches.get(
        (timezone or "").strip().lower()
    )


# -------------------------------------------------------
#                  TIMEZONE GROUPS
# -------------------------------------------------------

def get_timezone_regions(
    timezones=None
):
    timezones = timezones or get_cached_timezones()

    return sorted({
        timezone.split("/")[0]
        if "/" in timezone
        else "Other"
        for timezone in timezones
    })


def get_region_timezones(
    region,
    timezones=None
):
    timezones = timezones or get_cached_timezones()

    if region == "Other":
        return [
            timezone
            for timezone in timezones
            if "/" not in timezone
        ]

    return [
        timezone
        for timezone in timezones
        if timezone.startswith(
            f"{region}/"
        )
    ]