from flask import Flask, render_template, request, jsonify, make_response, send_file
from src.configurations import PORT
from src.utils import register_new_student, get_timestamp_image, convert_datetime_timestamp, extract_faces_and_encode, get_attendance_stats, download_excel_file
import shutil
import os
import cv2
from openpyxl import load_workbook


app = Flask("attendance-monitoring-system")


@app.route('/status', methods=["GET"])
def status():
    return {'attendance-monitoring-system': 'OK'}


@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/register_student', methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
        campus_id = request.form["campus_id"]
        student_name = request.form["student_name"]
        profile_img = request.files["profile_image"]
        image_path = "data/images/{}.JPG".format(str(campus_id))
        with open(image_path, 'wb') as img_file:
            shutil.copyfileobj(profile_img, img_file)
            img_file.close()
        msg = register_new_student(campus_id, student_name, image_path)
        return make_response(jsonify(msg), 200)
    else:
        return render_template("studentRegisteration.html")


@app.route('/record_attendance', methods=["GET", "POST"])
def record_attendance():
    if request.method == "POST":
        class_image = request.files["class_image"]
        # flask.request.files.getlist(
        image_path = "data/classroom_images/temp.JPG"
        with open(image_path, 'wb') as img_file:
            shutil.copyfileobj(class_image, img_file)
            img_file.close()
        date_time = get_timestamp_image(image_path)
        timestamp = convert_datetime_timestamp(date_time)
        timestamp_name = "data/classroom_images/{}.JPG".format(timestamp)
        os.rename("data/classroom_images/temp.JPG", timestamp_name)

        classroom_image = cv2.imread(timestamp_name)
        faces_encs, faces_locs = extract_faces_and_encode(classroom_image)
        msg = get_attendance_stats(class_image, timestamp, faces_encs, faces_locs)

        return make_response(jsonify(msg), 200)

    else:
        return render_template("recordAttendance.html")


@app.route('/download_attendance_record', methods=["GET"])
def download_attendance_record():
    excel_path = download_excel_file()
    wb = load_workbook(excel_path)
    wb.save(excel_path)
    return send_file(excel_path)


if __name__ == '__main__':
    app.run(debug=True, port=PORT)
