try:
    from flask import Flask, render_template, request
except Exception as e:
    raise RuntimeError(
        "Flask is not installed or could not be imported. Install it with: pip install Flask"
    ) from e

import subprocess
import os
import sys

app = Flask(__name__)

# Create users.txt if it doesn't exist
if not os.path.exists("users.txt"):
    open("users.txt", "w").close()

# ---------------- LOGIN ----------------

@app.route("/", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        with open("users.txt", "r") as file:
            users = file.readlines()

        for user in users:
            try:
                u, p = user.strip().split(",")
                if username == u and password == p:
                    print("Launching Air Writing...")
                    subprocess.Popen(
                        [sys.executable, "air_writing.py"],
                        cwd=os.path.dirname(os.path.abspath(__file__))
                    )
                    return render_template("success.html")
            except Exception as e:
                print("Error:", e)

        error = "Invalid Username or Password"

    return render_template("login.html", error=error)

# ---------------- REGISTER ----------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        with open("users.txt", "r") as file:
            users = file.readlines()

        for user in users:
            try:
                u, p = user.strip().split(",")
                if username == u:
                    return """
                    <h2>User Already Exists</h2>
                    <br>
                    <a href='/register'>
                    Back
                    </a>
                    """
            except:
                pass

        with open("users.txt", "a") as file:
            file.write(f"{username},{password}\n")

        return """
        <h2>Registration Successful</h2>
        <br>
        <a href='/'>
        Login Now
        </a>
        """

    return render_template("register.html")

# ---------------- START ----------------

if __name__ == "__main__":
    app.run(debug=True)
