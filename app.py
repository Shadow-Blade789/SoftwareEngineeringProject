from flask import Flask, render_template, request
from scheduler.csv_reader import read_teams
from scheduler.schedule_generator import generate_schedule

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
 
            schedule = generate_schedule(teams, tables, runs_per_team=3, start_time=start_time)
            return render_template("schedule.html", schedule=schedule, teams=teams, tables=tables)

        except ValueError as e:
            error = str(e)

        except Exception as e:
            error = f"Error processing file: {e}"

    return render_template(
        "index.html",
        error=error
    )

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)