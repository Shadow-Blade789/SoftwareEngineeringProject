from flask import Flask, render_template, request, redirect, url_for
import os, csv, io

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    file = request.files.get("file")

    if not file:
        return "No file uploaded"

    text = file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        print(row)
    return "CSV read successfully"

if __name__ == "__main__":
    app.run(debug=True)