from flask import Flask, render_template, request
from scheduler.csv_reader import read_teams
from scheduler.scheduler import generate_schedule

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    error = None

    if request.method == "POST":
        file = request.files.get("file")
        tables_raw = request.form.get("tables", "").strip()
        start_time = request.form.get("start_time", "09:00")

        try:
            tables = int(tables_raw)
            if tables < 1:
                raise ValueError

        except ValueError:
            error = "Please enter a valid number of tables."
            return render_template("index.html", error=error)

        if not file or not file.filename:
            error = "Please select a CSV file."
            return render_template("index.html", error=error)

        if not file.filename.lower().endswith(".csv"):
            error = "Please upload a CSV file."
            return render_template("index.html", error=error)

        try:
            teams = read_teams(file.stream)
            if len(teams) == 0:
                raise ValueError("No teams were found in the CSV.")
#AI Code Begins
            schedule = generate_schedule(teams, tables, start_time=start_time) # Generate schedule
            table_numbers = sorted(set(match["table"] for match in schedule))
            times = sorted(set(match["time"] for match in schedule))
            schedule_grid = {}

            for time in times:
                schedule_grid[time] = {}

                for table in table_numbers:
                    schedule_grid[time][table] = None

            for match in schedule:
                schedule_grid[match["time"]][match["table"]] = match

            return render_template("schedule.html", schedule=schedule, tables=table_numbers, times=times, schedule_grid=schedule_grid)
#AI Code Ends
        except ValueError as e:
            error = str(e)

        except Exception as e:
            error = f"Error processing file: {e}"

    return render_template("index.html", error=error)

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)