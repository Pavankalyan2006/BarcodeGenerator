from flask import Flask, render_template, request, send_file, redirect, url_for
import qrcode
import barcode
from barcode.writer import ImageWriter
import os
from pymongo import MongoClient
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder for car images
UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Ensure 'codes' directory exists for QR/Barcodes
CODE_FOLDER = "static/codes"
if not os.path.exists(CODE_FOLDER):
    os.makedirs(CODE_FOLDER)

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client["cardatabase"]
cars_collection = db["information"]

@app.route("/")
def index():
    return render_template("index.html", car=None, img_path=None)

@app.route("/generate", methods=["POST"])
def generate():
    make = request.form["make"]
    model = request.form["model"]
    year = request.form["year"]
    color = request.form["color"]
    vin = request.form["vin"]
    reg_no = request.form["reg_no"]
    engine_no = request.form["engine_no"]
    owner = request.form["owner"]
    fuel_type = request.form["fuel_type"]
    transmission = request.form["transmission"]
    chassis_no = request.form["chassis_no"]
    code_type = request.form["code_type"]
    car_image = request.files["car_image"]  # Get uploaded image

    # Check if registration number already exists
    if cars_collection.find_one({"reg_no": reg_no}):
        return "Error: Registration Number already exists!", 400

    # Save car image
    if car_image:
        filename = secure_filename(car_image.filename)
        img_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        car_image.save(img_path)
    else:
        img_path = None

    # Store full car details in MongoDB
    car_document = {
        "make": make, "model": model, "year": year, "color": color, "vin": vin,
        "reg_no": reg_no, "engine_no": engine_no, "owner": owner, "fuel_type": fuel_type,
        "transmission": transmission, "chassis_no": chassis_no, "car_image": img_path
    }
    cars_collection.insert_one(car_document)

    # Generate structured car details for QR/Barcode
    car_data = (
        f"Make: {make}\nModel: {model}\nYear: {year}\nColor: {color}\n"
        f"VIN: {vin}\nReg No: {reg_no}\nEngine No: {engine_no}\n"
        f"Owner: {owner}\nFuel Type: {fuel_type}\nTransmission: {transmission}\n"
        f"Chassis No: {chassis_no}"
    )

    # Generate Barcode or QR Code
    filename = f"{CODE_FOLDER}/{reg_no}"
    img_code_path = ""
    try:
        if code_type == "barcode":
            barcode_class = barcode.get_barcode_class("code128")
            barcode_instance = barcode_class(reg_no, writer=ImageWriter())  # Barcode only supports short text
            img_code_path = f"{filename}.png"
            barcode_instance.save(filename)
        else:
            qr = qrcode.make(car_data)
            img_code_path = f"{filename}_qr.png"
            qr.save(img_code_path)
    except Exception as e:
        return f"Error generating code: {str(e)}", 500

    return render_template("index.html", car=car_document, img_path=img_code_path)

@app.route("/download/<filename>")
def download(filename):
    return send_file(f"static/codes/{filename}", as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
