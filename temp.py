from flask import Flask, request, jsonify, render_template
import os
from werkzeug.utils import secure_filename
import pytesseract
import cv2
import firebase_admin
from firebase_admin import credentials, db

# Initialize Flask app
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

pytesseract.pytesseract.tesseract_cmd = r'C://Program Files//Tesseract-OCR//tesseract.exe'

cred = credentials.Certificate("fire_base_credential")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'fire_base_url'
})

print("Firebase initialized successfully")

def extract_text(image_path):
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    processed_image = cv2.threshold(gray_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    extracted_text = pytesseract.image_to_string(processed_image, lang='eng', config='--psm 6')
    print(f"Extracted Text: {extracted_text}")  # Log extracted text
    return extracted_text

def parse_text(extracted_text):
    parsed_data = {}
    lines = extracted_text.split("\n")
    for line in lines:
        if ":" in line:
            key, value = line.split(":", 1)
            parsed_data[key.strip()] = value.strip()
    print(f"Parsed Data: {parsed_data}")
    return parsed_data


def save_to_firebase(parsed_data):
    try:
        print("Saving data to Firebase Realtime Database...")  # Log before saving
        ref = db.reference('candidates')
        ref.push(parsed_data)
        print("Data saved successfully")
    except Exception as e:
        print(f"Error saving to Firebase: {e}")


@app.route('/')
def index():
    return render_template('upload_form.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'formFile' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['formFile']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            extracted_text = extract_text(filepath)
            parsed_data = parse_text(extracted_text)
            save_to_firebase(parsed_data)
            return jsonify({'message': 'File processed and data stored successfully.'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file type'}), 400

if __name__ == '__main__':
    app.run(debug=True)
