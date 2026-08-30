from functools import lru_cache
from importlib.resources import files
from zoneinfo import ZoneInfo, available_timezones


# -------------------------------------------------------
#                  TIMEZONE PROVIDER
# -------------------------------------------------------

TIMEZONE_HELP_URL = "https://www.iana.org/time-zones"

USER_FACING_REGIONS = (
    "Africa",
    "America",
    "Antarctica",
    "Asia",
    "Atlantic",
    "Australia",
    "Europe",
    "Indian",
    "Pacific"
)


def _zoneinfo_timezones():
    return sorted(
        available_timezones()
    )


def get_cached_timezones():
    return _zoneinfo_timezones()


async def get_available_timezones():
    return get_cached_timezones()


@lru_cache(maxsize=1)
def get_timezone_links():
    try:
        timezone_data = files("tzdata").joinpath("zoneinfo/tzdata.zi")
        links = {}
        for line in timezone_data.read_text(encoding="utf-8").splitlines():
            if not line.startswith("L "):
                continue

            _, target, alias = line.split(maxsplit=2)
            links[alias] = target
        return links
    except (FileNotFoundError, ModuleNotFoundError, OSError):
        return {}


def get_canonical_timezone(timezone):
    if not timezone:
        return None

    try:
        ZoneInfo(timezone)
    except (KeyError, ValueError):
            return timezone

    links = get_timezone_links()
    canonical = timezone
    seen = set()
    while canonical in links and canonical not in seen:
        seen.add(canonical)
        canonical = links[canonical]

    return canonical


def get_browse_timezones(timezones=None):
    timezones = timezones or get_cached_timezones()
    return [
        timezone
        for timezone in timezones
        if (
            timezone == get_canonical_timezone(timezone)
            and timezone.split("/", 1)[0] in USER_FACING_REGIONS
        )
    ]


# -------------------------------------------------------
#                  TIMEZONE SEARCH
# -------------------------------------------------------

async def search_timezones(
    search: str,
    limit=None
):
    normalized_search = (
        (search or "")
        .strip()
        .lower()
        .replace("_", " ")
    )

    if not normalized_search:
        return []

    timezones = await get_available_timezones()
    exact_matches = []
    city_matches = []
    prefix_matches = []
    partial_matches = []

    for timezone in timezones:
        canonical = get_canonical_timezone(timezone)
        if (
            canonical is None
            or canonical.split("/", 1)[0] not in USER_FACING_REGIONS
        ):
            continue

        source = timezone.lower().replace("_", " ")
        canonical_text = canonical.lower().replace("_", " ")
        label, _ = get_timezone_display(canonical)
        display = label.lower()
        region_display = (
            f"{canonical.split('/')[0]}/{label}"
        ).lower()

        if normalized_search in (source, canonical_text, display, region_display):
            exact_matches.append(canonical)
        elif display == normalized_search:
            city_matches.append(canonical)
        elif display.startswith(normalized_search):
            prefix_matches.append(canonical)
        elif (
            normalized_search in source
            or normalized_search in canonical_text
            or normalized_search in display
        ):
            partial_matches.append(canonical)

    results = (
        exact_matches
        + city_matches
        + prefix_matches
        + partial_matches
    )

    results = list(dict.fromkeys(results))
    results = sort_timezones_for_display(results)
    return results[:limit] if limit is not None else results

async def validate_timezone(
    timezone: str
):
    timezones = await get_available_timezones()
    matches = {
        value.lower(): value
        for value in timezones
    }

    match = matches.get(
        (timezone or "").strip().lower()
    )
    return get_canonical_timezone(match) if match else None


# -------------------------------------------------------
#                  TIMEZONE GROUPS
# -------------------------------------------------------

def get_timezone_regions(
    timezones=None
):
    browse_timezones = get_browse_timezones(timezones)
    regions = [
        region
        for region in USER_FACING_REGIONS
        if any(timezone.startswith(f"{region}/") for timezone in browse_timezones)
    ]

    if not regions and any("/" not in timezone for timezone in (timezones or [])):
        regions.append("Other")

    return regions


def get_region_timezones(
    region,
    timezones=None
):
    timezones = timezones or get_cached_timezones()
    browse_timezones = get_browse_timezones(timezones)

    if region == "Other":
        return [
            timezone
            for timezone in timezones
            if "/" not in timezone
        ]

    region_timezones = [
        timezone
        for timezone in browse_timezones
        if timezone.startswith(
            f"{region}/"
        )
    ]

    return sort_timezones_for_display(region_timezones)


def get_timezone_display(timezone):
    parts = timezone.split("/")
    label = parts[-1].replace("_", " ")
    description = " / ".join(
        part.replace("_", " ")
        for part in parts[1:-1]
    )

    return label, description


def sort_timezones_for_display(timezones):
    return sorted(
        timezones,
        key=lambda timezone: (
            get_timezone_display(timezone)[0].lower(),
            timezone.lower()
        )
    )


def get_timezone_option_description(timezone, timezones):
    label, description = get_timezone_display(timezone)
    label_count = sum(
        get_timezone_display(value)[0] == label
        for value in timezones
    )

    return description if label_count > 1 else None