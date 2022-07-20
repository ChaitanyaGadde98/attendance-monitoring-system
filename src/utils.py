import face_recognition
import cv2
import numpy as np
import os
import pandas as pd
from PIL import Image
import time
import datetime
from src.configurations import REGISTRATIONS_PICKLE_PATH, PICKLE_FILENAME, DIST_THRESHOLD, DRAW_BOX, ATTENDANCE_REPORT_PATH, ATTENDANCE_EXCEL_PATH


def get_timestamp_image(path):
    return Image.open(path)._getexif()[36867]


def convert_datetime_timestamp(time_str):
    return str(int(time.mktime(datetime.datetime.strptime(time_str, "%Y:%m:%d %H:%M:%S").timetuple())))


def get_datetime_from_timestamp(timestamp):
    return datetime.datetime.fromtimestamp(int(timestamp)).strftime('"%Y:%m:%d %H:%M:%S"')


def check_registration_data(REGISTRATIONS_PICKLE_PATH, PICKLE_FILENAME):
    path = os.path.join(REGISTRATIONS_PICKLE_PATH, PICKLE_FILENAME)
    abs_path = os.path.join(os.getcwd(), path)
    if os.path.exists(abs_path):
        return abs_path
    else:
        data = pd.DataFrame(columns=["ID", "name", "image_path", "image_encoding"], data=[])
        data.to_pickle(abs_path)
        return abs_path


def register_new_student(id, name, image_path):
    path = check_registration_data(REGISTRATIONS_PICKLE_PATH, PICKLE_FILENAME)
    registration_df = pd.read_pickle(path)
    if not (registration_df['ID'] == id).any():
        image_encoding = get_face_encoding(image_path)
        registration_df.loc[len(registration_df.index)] = [id, name, image_path, image_encoding]
        registration_df.to_pickle(path)
        print("Student ID - {} successfully registred.".format(id))
        return {"msg": "Student ID - {} successfully registred.".format(id)}
    else:
        print("Student ID - {} already registred.".format(id))
        return {"msg": "Student ID - {} already registred.".format(id)}


def get_face_encoding(img_path):
    image = face_recognition.load_image_file(img_path)
    image_encodings = face_recognition.face_encodings(image)[0]
    return image_encodings


def extract_faces_and_encode(class_img):
    faces_locs = face_recognition.face_locations(class_img)
    faces_encs = face_recognition.face_encodings(class_img, faces_locs)
    return faces_encs, faces_locs


def get_attendance_stats(class_img, timestamp, class_encs, class_face_locs):
    path = check_registration_data(REGISTRATIONS_PICKLE_PATH, PICKLE_FILENAME)
    registration_df = pd.read_pickle(path)
    attendance_makered = {}
    registered_names = registration_df["name"].to_list()
    registered_ids = registration_df["ID"].to_list()
    registered_encodings = registration_df["image_encoding"].to_list()
    for (top, right, bottom, left), face_encoding in zip(class_face_locs, class_encs):
        matches = face_recognition.compare_faces(registered_encodings, face_encoding)
        student_name = None
        student_id = None
        face_distances = face_recognition.face_distance(registered_encodings, face_encoding)
        if min(face_distances) < DIST_THRESHOLD:
            min_dist_idx = np.argmin(face_distances)
            print(face_distances, min_dist_idx)
            if matches[min_dist_idx]:
                student_name = registered_names[min_dist_idx]
                student_id = registered_ids[min_dist_idx]

        if student_name is not None:
            if  DRAW_BOX:
                class_img = mark_detected_faces_on_image(class_img, student_name, left, top, right, bottom)

            attendance_makered[student_id] = student_name
            print("Attendance for ID: {} - Name: {} recorded".format(student_id, student_name))

    attendees = list(attendance_makered.keys())
    update_attendance(registration_df, timestamp, attendees)
    if bool(attendance_makered):
        return attendance_makered


def mark_detected_faces_on_image(img, student_name, left, top, right, bottom):
    cv2.rectangle(img, (left, top), (right, bottom), (0, 255, 0), 2)
    cv2.rectangle(img, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(img, student_name, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 1)
    return img


def update_attendance(registered_df, timestamp, attendees):
    if not os.path.exists(ATTENDANCE_REPORT_PATH):
        cols = ["timestamp", "date_time"]
        cols.extend(registered_df["ID"].to_list())
        attendance_records_DF = pd.DataFrame(columns=cols, data=[])
        attendance_records_DF.to_csv(ATTENDANCE_REPORT_PATH, index=False)

    attendance_records_DF = pd.read_csv(ATTENDANCE_REPORT_PATH, index_col=None)
    date_time = get_datetime_from_timestamp(timestamp)

    if not ((attendance_records_DF['timestamp'] == int(timestamp)) & (attendance_records_DF['date_time'] == date_time)).any():
        temp_row = [timestamp, date_time]
        IDs = registered_df["ID"].to_list()
        temp = [1 if ID in attendees else 0 for ID in IDs]
        temp_row.extend(temp)
        attendance_records_DF.loc[len(attendance_records_DF.index)] = temp_row
        attendance_records_DF.to_csv(ATTENDANCE_REPORT_PATH, index=False)


def download_excel_file():
    excel_DF = pd.read_csv(ATTENDANCE_REPORT_PATH)
    excel_writer = pd.ExcelWriter(ATTENDANCE_EXCEL_PATH)
    excel_DF.to_excel(excel_writer, index=False)
    excel_writer.save()
    return ATTENDANCE_EXCEL_PATH








