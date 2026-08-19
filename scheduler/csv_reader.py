import csv

def read_teams(file):
    teams = []
    reader = csv.DictReader(file.read().decode("utf-8-sig").splitlines())

    if not reader.fieldnames:
        raise ValueError("The CSV file is empty.")

    required_columns = ["Team Number", "Team Name"]
    missing_columns = [
        column
        for column in required_columns
        if column not in reader.fieldnames
    ]

    if missing_columns:
        raise ValueError("Missing CSV columns: " + ", ".join(missing_columns))

    for row_number, row in enumerate(reader, start=2):
        team_number = (row["Team Number"].strip())
        team_name = (row["Team Name"].strip())

        if not team_number:
            raise ValueError(f"Row {row_number} has no team number.")

        if not team_name:
            raise ValueError(f"Row {row_number} has no team name.")

        teams.append({"number": team_number, "name": team_name})

    if not teams:
        raise ValueError("No teams were found in the CSV.")

    return teams