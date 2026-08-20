from ortools.sat.python import cp_model #External library for creating a schedule
from scheduler.settings import (RUNS_PER_TEAM, SLOT_LENGTH, SOLVER_TIME_LIMIT)
import math

def generate_schedule(teams, tables, start_time):
    number_of_runs = len(teams) * RUNS_PER_TEAM
    minimum_slots = math.ceil(number_of_runs / tables)
    number_of_slots = math.ceil(minimum_slots + len(teams) / tables)

    model = cp_model.CpModel() #creating the OR-Tools model

    run_slots = {} #to save each teams runs slots

    # Create variables
    for team_index, team in enumerate(teams):
        run_slots[team_index] = []
        
        for run in range(RUNS_PER_TEAM):
            slot = model.NewIntVar(0, number_of_slots - 1, f"team_{team_index}_run_{run}") #integer from slot 0 to final slot
            run_slots[team_index].append(slot) #save the run into the dictionary run slots

    # Each team's runs must happen at different times
    for team_index in run_slots:
        model.AddAllDifferent(run_slots[team_index])

    # Limit number of teams running at each slot
    for slot_index in range(number_of_slots):
        slot_assignments = []
        for team_index in run_slots:
            for run in range(RUNS_PER_TEAM):
                is_in_slot = model.NewBoolVar(f"team_{team_index}_run_{run}_slot_{slot_index}")

                model.Add(run_slots[team_index][run] == slot_index).OnlyEnforceIf(is_in_slot)
                model.Add(run_slots[team_index][run] != slot_index).OnlyEnforceIf(is_in_slot.Not())

                slot_assignments.append(is_in_slot)

        model.Add(sum(slot_assignments) <= tables)
        
        solver = cp_model.CpSolver() #Start the solver
        solver.parameters.max_time_in_seconds = SOLVER_TIME_LIMIT #ensure a timeout so it doesnt try to find a better one forever
        status = solver.Solve(model)
        
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE): #checking to see if it actually made a schedule
            raise ValueError("Unable to create a schedule.")
        
        return run_slots #returns the schedule to be used