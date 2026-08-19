import math
import random
from collections import defaultdict
from datetime import datetime, timedelta


MATCH_DURATION = 2.5
SCORE_AND_CHANGEOVER = 2.5
CONTINGENCY_BUFFER = 1

SLOT_DURATION = (
    MATCH_DURATION
    + SCORE_AND_CHANGEOVER
    + CONTINGENCY_BUFFER
)


SHORT_BREAK = 20
VERY_SHORT_BREAK = 12


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


def calculate_break_minutes(
    first_slot,
    second_slot
):
    elapsed_time = (
        second_slot - first_slot
    ) * SLOT_DURATION

    break_time = (
        elapsed_time
        - MATCH_DURATION
    )

    return round(
        break_time,
        1
    )


def calculate_candidate_penalty(
    team,
    slot,
    assignments,
    total_slots
):
    previous_runs = assignments[team]

    if not previous_runs:
        return 0

    penalty = 0

    ideal_gap = (
        total_slots / 3
    )

    for previous_slot in previous_runs:

        slot_gap = (
            slot
            - previous_slot
        )

        break_minutes = (
            calculate_break_minutes(
                previous_slot,
                slot
            )
        )

        # Consecutive scheduling.
        if slot_gap == 1:
            penalty += 10000

        # Extremely short break.
        elif break_minutes < VERY_SHORT_BREAK:
            penalty += 1000

        # Short break.
        elif break_minutes < SHORT_BREAK:
            penalty += 150

        # Encourage even spacing.
        penalty += (
            abs(
                slot_gap
                - ideal_gap
            )
            * 5
        )

    return penalty


def generate_candidate(
    teams,
    number_of_tables,
    runs_per_team,
    seed
):
    random_generator = random.Random(
        seed
    )

    team_numbers = [
        team["number"]
        for team in teams
    ]

    total_runs, total_slots = (
        calculate_schedule_size(
            len(team_numbers),
            number_of_tables,
            runs_per_team
        )
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

    remaining_runs = {
        team: runs_per_team
        for team in team_numbers
    }

    for slot_index in range(
        total_slots
    ):

        available_teams = [
            team
            for team in team_numbers
            if remaining_runs[team] > 0
            and (
                not assignments[team]
                or assignments[team][-1]
                != slot_index - 1
            )
        ]

        # Randomise before scoring.
        random_generator.shuffle(
            available_teams
        )

        selected = []

        while (
            len(selected)
            < number_of_tables
            and available_teams
        ):

            best_team = None
            best_score = None

            for team in available_teams:

                score = calculate_candidate_penalty(
                    team,
                    slot_index,
                    assignments,
                    total_slots
                )

                # Prefer teams with more remaining
                # runs so they don't get trapped later.
                score += (
                    remaining_runs[team]
                    * 0.25
                )

                score += (
                    random_generator.random()
                    * 2
                )

                if (
                    best_score is None
                    or score < best_score
                ):

                    best_score = score
                    best_team = team

            if best_team is None:
                break

            selected.append(
                best_team
            )

            available_teams.remove(
                best_team
            )

        # If the hard constraint prevented enough
        # teams from being selected, fill the slot
        # with the best remaining teams.
        if len(selected) < number_of_tables:

            fallback_teams = [
                team
                for team in team_numbers
                if remaining_runs[team] > 0
                and team not in selected
            ]

            random_generator.shuffle(
                fallback_teams
            )

            fallback_teams.sort(
                key=lambda team:
                calculate_candidate_penalty(
                    team,
                    slot_index,
                    assignments,
                    total_slots
                )
            )

            for team in fallback_teams:

                if len(selected) >= number_of_tables:
                    break

                selected.append(
                    team
                )

        # Put selected teams onto the tables.
        for table_index, team in enumerate(
            selected
        ):

            run_number = (
                run_counts[team]
                + 1
            )

            schedule[
                slot_index
            ][table_index]["team"] = team

            schedule[
                slot_index
            ][table_index]["run"] = (
                run_number
            )

            assignments[team].append(
                slot_index
            )

            assignments[team].sort()

            run_counts[team] += 1
            remaining_runs[team] -= 1

    # If we haven't assigned every run, repair
    # the candidate using remaining capacity.
    unassigned = []

    for team in team_numbers:

        while remaining_runs[team] > 0:

            unassigned.append(
                team
            )

            remaining_runs[team] -= 1

    for team in unassigned:

        best_option = None

        for slot_index in range(
            total_slots
        ):

            for table_index in range(
                number_of_tables
            ):

                cell = schedule[
                    slot_index
                ][table_index]

                if cell["team"] is not None:
                    continue

                score = (
                    calculate_candidate_penalty(
                        team,
                        slot_index,
                        assignments,
                        total_slots
                    )
                )

                if best_option is None:
                    best_option = (
                        score,
                        slot_index,
                        table_index
                    )

                elif score < best_option[0]:
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

    total_penalty = 0
    total_breaks = 0

    consecutive_runs = 0
    very_short_breaks = 0
    short_breaks = 0

    all_breaks = []

    for team, runs in assignments.items():

        for first, second in zip(
            runs,
            runs[1:]
        ):

            total_breaks += 1

            slot_gap = (
                second - first
            )

            break_minutes = (
                calculate_break_minutes(
                    first,
                    second
                )
            )

            all_breaks.append(
                break_minutes
            )

            if slot_gap == 1:

                consecutive_runs += 1

                total_penalty += 100

            elif break_minutes < VERY_SHORT_BREAK:

                very_short_breaks += 1

                total_penalty += 40

            elif break_minutes < SHORT_BREAK:

                short_breaks += 1

                total_penalty += 15

            # Encourage longer breaks.
            total_penalty += max(
                0,
                SHORT_BREAK - break_minutes
            ) * 0.5

    if not all_breaks:
        quality = 100

        minimum_break = None
        average_break = None
        maximum_break = None

    else:

        minimum_break = min(
            all_breaks
        )

        average_break = round(
            sum(all_breaks)
            / len(all_breaks),
            1
        )

        maximum_break = max(
            all_breaks
        )

        maximum_possible_penalty = (
            total_breaks
            * 50
        )

        quality = (
            100
            - (
                total_penalty
                / maximum_possible_penalty
                * 100
            )
        )

        quality = max(
            0,
            min(
                100,
                round(quality)
            )
        )

    return {
        "quality": quality,
        "minimum_break": minimum_break,
        "average_break": average_break,
        "maximum_break": maximum_break,
        "short_breaks": short_breaks,
        "very_short_breaks": (
            very_short_breaks
        ),
        "consecutive_runs": (
            consecutive_runs
        )
    }


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
    attempts=1000
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

    total_runs, total_slots = (
        calculate_schedule_size(
            len(teams),
            number_of_tables,
            runs_per_team
        )
    )

    total_positions = (
        total_slots
        * number_of_tables
    )

    if total_positions < total_runs:
        raise ValueError(
            "There are not enough table positions "
            "to schedule all team runs."
        )

    best_schedule = None
    best_quality = -1

    best_report = None

    for attempt in range(attempts):

        candidate = generate_candidate(
            teams,
            number_of_tables,
            runs_per_team,
            seed=(
                attempt
                * 7919
                + len(teams)
                * 31
                + number_of_tables
            )
        )

        if candidate is None:
            continue

        report = calculate_quality(
            candidate
        )

        quality = report["quality"]

        if (
            best_schedule is None
            or quality > best_quality
        ):

            best_schedule = candidate
            best_quality = quality
            best_report = report

        # A perfect schedule cannot be improved.
        if (
            report["consecutive_runs"] == 0
            and report["very_short_breaks"] == 0
            and report["short_breaks"] == 0
            and quality >= 99
        ):
            break

    if best_schedule is None:
        raise ValueError(
            "Unable to generate a schedule."
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

    best_schedule["quality"] = (
        best_report["quality"]
    )

    best_schedule["minimum_break"] = (
        best_report["minimum_break"]
    )

    best_schedule["average_break"] = (
        best_report["average_break"]
    )

    best_schedule["maximum_break"] = (
        best_report["maximum_break"]
    )

    best_schedule["short_breaks"] = (
        best_report["short_breaks"]
    )

    best_schedule["very_short_breaks"] = (
        best_report["very_short_breaks"]
    )

    best_schedule["consecutive_runs"] = (
        best_report["consecutive_runs"]
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