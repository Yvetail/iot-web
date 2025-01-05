from flask import Flask, render_template, jsonify
import firebase_admin
from firebase_admin import credentials, db
import pickle
import numpy as np
from datetime import datetime

app = Flask(__name__)

# Initialize Firebase Admin
cred = credentials.Certificate("D:\code-project\iot-web\ixiotml-firebase-adminsdk-6wgza-d3038d371f.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://fixiotml-default-rtdb.asia-southeast1.firebasedatabase.app/'
})

# Path file JSON untuk menyimpan data lokal
JSON_FILE_PATH = 'air_quality_data.json'

# Fungsi untuk menulis data ke file JSON
def write_json(path, json_data):
    with open(path, 'w') as file_out:
        json.dump(json_data, file_out, indent=4)

# Fungsi untuk membaca data dari file JSON
def read_json(path):
    try:
        with open(path) as file_in:
            return json.load(file_in)
    except FileNotFoundError:
        return {}


# Fungsi untuk memperbarui file JSON dengan data baru dari Firebase
def update_local_storage():
    # Muat data lokal
    local_data = read_json(JSON_FILE_PATH)

    # Ambil data dari Firebase
    firebase_data = fetch_firebase_data()
    if not firebase_data:
        return "No data from Firebase"

    # Gabungkan data baru dari Firebase dengan data lokal
    for key, value in firebase_data.items():
        if key not in local_data:
            local_data[key] = value

    # Simpan data yang diperbarui ke file JSON
    write_json(JSON_FILE_PATH, local_data)
    return "Local storage updated"

# Load the ML model
with open('model.pkl', 'rb') as file:
    model = pickle.load(file)

# Air Quality Thresholds (matching ESP32 thresholds)
GOOD_THRESHOLD = 450
MODERATE_THRESHOLD = 500


def get_air_quality_status(value):
    if value <= GOOD_THRESHOLD:
        return "Good", "green"
    elif value <= MODERATE_THRESHOLD:
        return "Moderate", "yellow"
    else:
        return "Bad", "red"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get_sensor_data')
def get_sensor_data():
    try:
        # Get real-time data from Firebase
        ref = db.reference('/')
        data = ref.get()

        air_quality = data.get('AirQuality', 0)
        status, led_color = get_air_quality_status(air_quality)

        # Update LED status in Firebase
        led_status = {
            'LED_GREEN': led_color == 'green',
            'LED_YELLOW': led_color == 'yellow',
            'LED_RED': led_color == 'red',
            'FAN': led_color == 'red'  # Fan turns on when air quality is bad
        }

        # Update LED status in Firebase
        db.reference('/LED_Status').set(led_status)

        # Make prediction automatically
        features = np.array([[
            data.get('Temperature', 0),
            data.get('Humidity', 0),
            air_quality
        ]])
        prediction = model.predict(features)[0]

        return jsonify({
            'success': True,
            'airQuality': air_quality,
            'temperature': data.get('Temperature', 0),
            'humidity': data.get('Humidity', 0),
            'status': status,
            'led_color': led_color,
            'prediction': str(prediction),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/predict')
def predict():
    try:
        # Get latest sensor data
        ref = db.reference('/')
        data = ref.get()

        # Prepare features for prediction
        features = np.array([[
            data.get('AirQuality', 0),
            data.get('Temperature', 0),
            data.get('Humidity', 0)
        ]])

        # Make prediction
        prediction = model.predict(features)[0]

        return jsonify({
            'success': True,
            'prediction': str(prediction),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True)