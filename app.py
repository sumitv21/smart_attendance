from flask import Flask, render_template, request, send_file, redirect, url_for, session
import os
import face_recognition
import numpy as np
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = "shree_ranga"  # Secret key for session

# Load known faces
known_face_encodings = []
known_face_names = []

def load_known_faces():
    global known_face_encodings, known_face_names
    known_face_encodings = []
    known_face_names = []

    dataset_path = 'dataset'
    for filename in os.listdir(dataset_path):
        if filename.endswith('.jpg') or filename.endswith('.png'):
            img = face_recognition.load_image_file(os.path.join(dataset_path, filename))
            encoding = face_recognition.face_encodings(img)
            if encoding:
                known_face_encodings.append(encoding[0])
                known_face_names.append(os.path.splitext(filename)[0])

load_known_faces()

@app.route('/')
def index():
    if 'teacher' not in session:
        return redirect('/login')
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['teacher'] = request.form['teacher']
        session['subject'] = request.form['subject']
        return redirect('/')
    return '''
        <form method="post">
            <h2>👨‍🏫 Teacher Login</h2>
            <label>Name:</label><br>
            <input name="teacher"><br><br>
            <label>Subject:</label><br>
            <input name="subject"><br><br>
            <input type="submit" value="Login">
        </form>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    if 'teacher' not in session:
        return redirect('/login')

    file = request.files['image']
    filepath = os.path.join('static', 'captured.jpg')
    file.save(filepath)

    image = face_recognition.load_image_file(filepath)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    present_students = []
    for face_encoding in face_encodings:
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]
            if name not in present_students:
                present_students.append(name)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    teacher_name = session.get("teacher")
    subject = session.get("subject")

    if os.path.exists("attendance.xlsx"):
        df = pd.read_excel("attendance.xlsx")
    else:
        df = pd.DataFrame(columns=["Name", "DateTime", "Teacher", "Subject"])

    for student in present_students:
        df = pd.concat([df, pd.DataFrame([[student, now, teacher_name, subject]],
                                         columns=["Name", "DateTime", "Teacher", "Subject"])],
                       ignore_index=True)

    df.to_excel("attendance.xlsx", index=False)

    return render_template("index.html", message="✅ Attendance Marked!", students=present_students)

@app.route('/add_student', methods=['POST'])
def add_student():
    name = request.form.get("name")
    image_file = request.files.get("image")

    if not name or not image_file:
        return "❌ Name or image not provided!"

    save_path = os.path.join("dataset", f"{name}.jpg")
    image_file.save(save_path)

    load_known_faces()
    return f"✅ {name} added successfully!"

@app.route('/download')
def download():
    return send_file("attendance.xlsx", as_attachment=True)

@app.route('/clear')
def clear():
    df = pd.DataFrame(columns=["Name", "DateTime", "Teacher", "Subject"])
    df.to_excel("attendance.xlsx", index=False)
    return render_template("index.html", message="🧹 Attendance sheet cleared!")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
