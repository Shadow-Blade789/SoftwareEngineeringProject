from ortools.sat.python import cp_model #External library for creating a schedule
from scheduler.settings import (RUNS_PER_TEAM, SLOT_LENGTH, SOLVER_TIME_LIMIT)
import math
from datetime import datetime, timedelta

def generate_schedule(teams, tables, start_time):
    number_of_runs = len(teams) * RUNS_PER_TEAM
    minimum_slots = math.ceil(number_of_runs / tables)
    number_of_slots = minimum_slots
    model = cp_model.CpModel() #creating the OR-Tools model

    run_slots = {} #to save each teams runs slots

    for team_index, team in enumerate(teams):    # Create variables to use to control the model
        run_slots[team_index] = []
        for run in range(RUNS_PER_TEAM):
            slot = model.NewIntVar(0, number_of_slots - 1, f"team_{team_index}_run_{run}") #integer from slot 0 to final slot
            run_slots[team_index].append(slot) #save the run into the dictionary run slots

    for team_index in run_slots:    # Ensuring each slot only has 1 team
        model.AddAllDifferent(run_slots[team_index])

    for slot_index in range(number_of_slots):    # Making sure there's enough teams in each slot to fit on all tables
        slot_assignments = []
        for team_index in run_slots:
            for run in range(RUNS_PER_TEAM):
                is_in_slot = model.NewBoolVar(f"team_{team_index}_run_{run}_slot_{slot_index}")

                model.Add(run_slots[team_index][run] == slot_index).OnlyEnforceIf(is_in_slot)
                model.Add(run_slots[team_index][run] != slot_index).OnlyEnforceIf(is_in_slot.Not())

                slot_assignments.append(is_in_slot)

        model.Add(sum(slot_assignments) <= tables)

    solver = cp_model.CpSolver()    # Start the solver
    solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT #timeout on solver time to ensure it doesn't think forever
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):    # Check to see if it actually made a schedule
        raise ValueError("Unable to create a schedule.")

    schedule = []    # Store the schedule in a usable format, instead of the OR-Tools format

    start = datetime.strptime(start_time, "%H:%M")

    for slot_index in range(number_of_slots):    # Go through every slot
        table_number = 1

        for team_index, team in enumerate(teams):        # Go through every team
            for run_index, run_slot in enumerate(run_slots[team_index]):# Go through every run
                assigned_slot = solver.Value(run_slot)
                
                if assigned_slot == slot_index: # Only add the run if it belongs in this slot
                    run_time = start + timedelta(minutes=assigned_slot * SLOT_LENGTH)

                    schedule.append({
                        "team_number": team["number"],
                        "team_name": team["name"],
                        "run": run_index + 1,
                        "slot": assigned_slot,
                        "time": run_time.strftime("%H:%M"),
                        "table": table_number
                    })

                    table_number += 1

    return schedule #returns the schedule to be used