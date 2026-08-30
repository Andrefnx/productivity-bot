from zoneinfo import available_timezones


# -------------------------------------------------------
#                  TIMEZONE PROVIDER
# -------------------------------------------------------

TIMEZONE_HELP_URL = "https://www.iana.org/time-zones"


def _zoneinfo_timezones():
    return sorted(
        available_timezones()
    )


def get_cached_timezones():
    return _zoneinfo_timezones()


async def get_available_timezones():
    return get_cached_timezones()


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
        lowered_timezone = timezone.lower().replace("_", " ")
        city = timezone.split("/")[-1].lower().replace("_", " ")
        display = get_timezone_display(timezone)[0].lower()

        if lowered_timezone == normalized_search or display == normalized_search:
            exact_matches.append(timezone)
        elif city == normalized_search:
            city_matches.append(timezone)
        elif city.startswith(normalized_search):
            prefix_matches.append(timezone)
        elif normalized_search in lowered_timezone:
            partial_matches.append(timezone)

    results = (
        exact_matches
        + city_matches
        + prefix_matches
        + partial_matches
    )

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

    region_timezones = [
        timezone
        for timezone in timezones
        if timezone.startswith(
            f"{region}/"
        )
    ]

    return sort_timezones_for_display(region_timezones)


def get_timezone_display(timezone):
    parts = timezone.split("/")
    region = parts[0].replace("_", " ")
    label = f"{region}/{parts[-1].replace('_', ' ')}"
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