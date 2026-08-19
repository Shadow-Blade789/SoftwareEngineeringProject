import math
import random
from collections import defaultdict
from datetime import datetime, timedelta


MATCH_DURATION = 2.5
SCORE_AND_CHANGEOVER = 2.5
CONTINGENCY_BUFFER = 2

SLOT_DURATION = (
    MATCH_DURATION
    + SCORE_AND_CHANGEOVER
    + CONTINGENCY_BUFFER
)


def calculate_schedule_size(
    number_of_teams,
    number_of_tables,
    runs_per_team
):
    total_runs = (
        number_of_teams
        * runs_per_team
    )

    total_slots = math.ceil(
        total_runs
        / number_of_tables
    )

    return total_runs, total_slots


def calculate_time(slot_number, start_time):
    start = datetime.strptime(
        start_time,
        "%H:%M"
    )

    time = start + timedelta(
        minutes=slot_number * SLOT_DURATION
    )

    return time.strftime(
        "%I:%M %p"
    ).lstrip("0")


def calculate_assignment_score(
    team,
    slot,
    assignments,
    total_slots
):
    previous_runs = assignments[team]

    if not previous_runs:
        return 0

    score = 0
    ideal_gap = total_slots / 3

    for previous_slot in previous_runs:
        gap = slot - previous_slot

        if gap <= 1:
            score += 1000

        elif gap == 2:
            score += 150

        else:
            score += abs(
                gap - ideal_gap
            ) * 3

    return score


def generate_candidate(
    teams,
    number_of_tables,
    runs_per_team,
    seed
):
    random_generator = random.Random(seed)

    team_numbers = [
        team["number"]
        for team in teams
    ]

    total_runs, total_slots = calculate_schedule_size(
        len(team_numbers),
        number_of_tables,
        runs_per_team
    )

    schedule = [
        [
            {
                "table": table,
                "team": None,
                "run": None,
                "team_name": None,
                "time": None
            }
            for table in range(
                1,
                number_of_tables + 1
            )
        ]
        for _ in range(total_slots)
    ]

    assignments = defaultdict(list)
    run_counts = defaultdict(int)

    team_order = team_numbers[:]

    random_generator.shuffle(
        team_order
    )

    for team in team_order:

        for _ in range(runs_per_team):

            best_option = None

            for slot_index in range(
                total_slots
            ):

                if slot_index in assignments[team]:
                    continue

                for table_index in range(
                    number_of_tables
                ):

                    cell = schedule[
                        slot_index
                    ][table_index]

                    if cell["team"] is not None:
                        continue

                    score = calculate_assignment_score(
                        team,
                        slot_index,
                        assignments,
                        total_slots
                    )

                    score += (
                        random_generator.random()
                        * 0.01
                    )

                    if (
                        best_option is None
                        or score < best_option[0]
                    ):

                        best_option = (
                            score,
                            slot_index,
                            table_index
                        )

            if best_option is None:
                return None

            (
                score,
                slot_index,
                table_index
            ) = best_option

            run_number = (
                run_counts[team]
                + 1
            )

            schedule[
                slot_index
            ][table_index]["team"] = team

            schedule[
                slot_index
            ][table_index]["run"] = run_number

            assignments[team].append(
                slot_index
            )

            assignments[team].sort()

            run_counts[team] += 1

    return {
        "slots": schedule,
        "assignments": assignments,
        "total_runs": total_runs,
        "total_slots": total_slots
    }


def calculate_quality(candidate):
    assignments = candidate["assignments"]
    total_slots = candidate["total_slots"]

    penalties = 0
    gaps = []

    for team, runs in assignments.items():

        for first, second in zip(
            runs,
            runs[1:]
        ):

            gap = second - first
            gaps.append(gap)

            if gap <= 1:
                penalties += 50

            elif gap == 2:
                penalties += 8

            ideal_gap = total_slots / 3

            penalties += (
                abs(
                    gap - ideal_gap
                )
                * 0.5
            )

    if not gaps:
        return 100

    maximum_penalty = (
        len(gaps)
        * 10
    )

    quality = (
        100
        - (
            penalties
            / maximum_penalty
            * 100
        )
    )

    return max(
        0,
        min(
            100,
            round(quality)
        )
    )


def calculate_breaks(assignments):
    gaps = []
    minimum_gap = None

    for positions in assignments.values():

        for first, second in zip(
            positions,
            positions[1:]
        ):

            gap = second - first

            gaps.append(gap)

            if minimum_gap is None:
                minimum_gap = gap

            else:
                minimum_gap = min(
                    minimum_gap,
                    gap
                )

    if gaps:

        average_gap = round(
            sum(gaps)
            / len(gaps),
            2
        )

    else:
        average_gap = 0

    return (
        minimum_gap,
        average_gap
    )


def add_schedule_times(
    schedule,
    start_time
):
    for slot_index, slot in enumerate(
        schedule
    ):

        time = calculate_time(
            slot_index,
            start_time
        )

        for cell in slot:
            cell["time"] = time


def generate_schedule(
    teams,
    number_of_tables,
    runs_per_team=3,
    start_time="09:00",
    attempts=500
):
    if not teams:
        raise ValueError(
            "At least one team is required."
        )

    if number_of_tables < 1:
        raise ValueError(
            "There must be at least one table."
        )

    if runs_per_team < 1:
        raise ValueError(
            "Runs per team must be at least 1."
        )

    try:
        datetime.strptime(
            start_time,
            "%H:%M"
        )

    except ValueError:
        raise ValueError(
            "Please enter a valid starting time."
        )

    best_schedule = None
    best_quality = -1

    for attempt in range(attempts):

        candidate = generate_candidate(
            teams,
            number_of_tables,
            runs_per_team,
            seed=(
                attempt * 7919
                + len(teams) * 31
                + number_of_tables
            )
        )

        if candidate is None:
            continue

        quality = calculate_quality(
            candidate
        )

        if quality > best_quality:

            best_schedule = candidate
            best_quality = quality

        if best_quality >= 100:
            break

    if best_schedule is None:
        raise ValueError(
            "Unable to generate a valid schedule."
        )

    team_lookup = {
        team["number"]: team
        for team in teams
    }

    for slot in best_schedule["slots"]:

        for cell in slot:

            if cell["team"] is not None:

                team = team_lookup[
                    cell["team"]
                ]

                cell["team_name"] = (
                    team["name"]
                )

    add_schedule_times(
        best_schedule["slots"],
        start_time
    )

    (
        minimum_gap,
        average_gap
    ) = calculate_breaks(
        best_schedule["assignments"]
    )

    best_schedule["quality"] = (
        best_quality
    )

    best_schedule["minimum_gap"] = (
        minimum_gap
    )

    best_schedule["average_gap"] = (
        average_gap
    )

    best_schedule["slot_duration"] = (
        SLOT_DURATION
    )

    best_schedule["match_duration"] = (
        MATCH_DURATION
    )

    best_schedule["score_and_changeover"] = (
        SCORE_AND_CHANGEOVER
    )

    best_schedule["contingency_buffer"] = (
        CONTINGENCY_BUFFER
    )

    best_schedule["start_time"] = (
        calculate_time(
            0,
            start_time
        )
    )

    last_slot = (
        best_schedule["total_slots"]
        - 1
    )

    best_schedule["end_time"] = (
        calculate_time(
            last_slot,
            start_time
        )
    )

    return best_schedule