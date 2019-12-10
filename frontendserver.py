#!/usr/bin/env python3

# Use flask to serve the static html file instead of using the python simple server.
# Gives control of what is actually served from the server, and allows us to do some
# preprocessing to the html file if we chose choose before it's delivered.
from flask import Flask
from flask import render_template

# creates a Flask application, named app
app = Flask(__name__)
app.config['ENV'] = 'development'

# a route where we will display a welcome message via an HTML template
@app.route("/")
def hello():
    message = "Hello, World"
    return render_template('monitoring_page.html', message=message)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=8000)
