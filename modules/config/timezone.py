from zoneinfo import (
    available_timezones
)


# -------------------------------------------------------
#                  TIMEZONE SEARCH
# -------------------------------------------------------

def search_timezones(
    search: str,
    limit: int = 25
):
    search = (
        search
        .strip()
        .lower()
        .replace(
            " ",
            "_"
        )
    )

    if not search:
        return []

    timezones = sorted(
        available_timezones()
    )

    exact_matches = []
    city_matches = []
    partial_matches = []

    for timezone in timezones:
        lowered_timezone = (
            timezone.lower()
        )

        city = (
            timezone
            .split("/")[-1]
            .lower()
        )

        readable_timezone = (
            timezone
            .replace(
                "_",
                " "
            )
            .lower()
        )

        readable_search = (
            search
            .replace(
                "_",
                " "
            )
        )

        if (
            lowered_timezone
            == search
        ):
            exact_matches.append(
                timezone
            )

        elif city == search:
            exact_matches.append(
                timezone
            )

        elif city.startswith(
            search
        ):
            city_matches.append(
                timezone
            )

        elif search in lowered_timezone:
            partial_matches.append(
                timezone
            )

        elif (
            readable_search
            in readable_timezone
        ):
            partial_matches.append(
                timezone
            )

    results = []

    for timezone in (
        exact_matches
        + city_matches
        + partial_matches
    ):
        if timezone not in results:
            results.append(
                timezone
            )

        if len(
            results
        ) >= limit:
            break

    return results