from flask import Flask, render_template, request, jsonify, make_response, send_file

app = Flask("attendance-monitoring-system")


@app.route('/status', methods=["GET"])
def status():
    return {'attendance-monitoring-system': 'OK'}


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


if __name__ == '__main__':
    app.run(debug=True, port=PORT)
