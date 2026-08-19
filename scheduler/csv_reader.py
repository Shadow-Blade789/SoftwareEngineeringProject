import csv
import io


NUMBER_HEADERS = {
    "team number",
    "team_number",
    "teamnumber",
    "number",
    "team id",
    "team_id",
    "id"
}

NAME_HEADERS = {
    "team name",
    "team_name",
    "teamname",
    "name"
}


def normalise_header(value):
    return " ".join(
        str(value)
        .strip()
        .lower()
        .replace("-", " ")
        .split()
    )


def find_column(fieldnames, candidates):
    for field in fieldnames:
        if normalise_header(field) in candidates:
            return field

    return None


def read_teams(file_stream):
    raw = file_stream.read()

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8-sig")

    if not raw.strip():
        raise ValueError("The CSV file is empty.")

    try:
        sample = raw[:4096]
        dialect = csv.Sniffer().sniff(sample)

    except csv.Error:
        dialect = csv.excel

    reader = csv.DictReader(
        io.StringIO(raw),
        dialect=dialect
    )

    if not reader.fieldnames:
        raise ValueError("Could not find the CSV header.")

    number_column = find_column(
        reader.fieldnames,
        NUMBER_HEADERS
    )

    name_column = find_column(
        reader.fieldnames,
        NAME_HEADERS
    )

    if not number_column:
        number_column = reader.fieldnames[0]

    if not name_column and len(reader.fieldnames) > 1:
        name_column = reader.fieldnames[1]

    teams = []
    seen = set()

    for row in reader:
        team_number = str(
            row.get(number_column, "")
        ).strip()

        if not team_number:
            continue

        if name_column:
            team_name = str(
                row.get(name_column, "")
            ).strip()

        else:
            team_name = f"Team {team_number}"

        if not team_name:
            team_name = f"Team {team_number}"

        if team_number in seen:
            raise ValueError(
                f"Duplicate team number: {team_number}"
            )

        seen.add(team_number)

        teams.append({
            "number": team_number,
            "name": team_name
        })

    if not teams:
        raise ValueError(
            "No teams could be read from the CSV."
        )

    return teams