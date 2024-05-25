from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
import cv2
import numpy as np
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['PROCESSED_FOLDER'] = PROCESSED_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(PROCESSED_FOLDER):
    os.makedirs(PROCESSED_FOLDER)

def process_image(image_path, threshold):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    # Assuming reference square with 1 cm sides
    reference_side_cm = 1.0
    
    # Virtual coordinates of the reference square in the image (example values)
    ref_top_left = (50, 50)
    ref_bottom_right = (150, 150)
    
    # Measure the side length of the reference square in pixels
    reference_side_px = ref_bottom_right[0] - ref_top_left[0]
    
    # Calculate pixels per cm
    pixels_per_cm = reference_side_px / reference_side_cm
    
    # Resize image to Full HD (1920x1080) while keeping aspect ratio
    image = cv2.resize(image, (1920, 1080))
    
    _, thresh_image = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contour_area_cm2 = 0
    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        contour_area = cv2.contourArea(largest_contour)
        
        # Convert pixel area to cm²
        contour_area_cm2 = (contour_area / (pixels_per_cm ** 2))
        contour_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        cv2.drawContours(contour_image, [largest_contour], -1, (0, 255, 0), 3)
    else:
        contour_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # Create a mask with 1 cm squares
    mask = np.zeros_like(contour_image)
    for i in range(0, mask.shape[0], int(pixels_per_cm)):
        cv2.line(mask, (0, i), (mask.shape[1], i), (255, 255, 255), 1)
    for j in range(0, mask.shape[1], int(pixels_per_cm)):
        cv2.line(mask, (j, 0), (j, mask.shape[0]), (255, 255, 255), 1)
    
    # Overlay the mask on the contour image
    combined_image = cv2.addWeighted(contour_image, 0.8, mask, 0.2, 0)

    combined_image_path = os.path.join(app.config['PROCESSED_FOLDER'], 'combined.jpg')
    cv2.imwrite(combined_image_path, combined_image)
    
    print(f"Image saved to {combined_image_path}")
    
    return combined_image_path, contour_area_cm2

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        app.logger.error('No file part')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        app.logger.error('No selected file')
        return redirect(request.url)
    
    if file:
        threshold = int(request.form['threshold'])
        app.logger.info(f'File uploaded: {file.filename}')
        app.logger.info(f'Threshold: {threshold}')
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        combined_image_path, contour_area_cm2 = process_image(file_path, threshold)
        
        return render_template('result.html', combined_image=combined_image_path, contour_area=contour_area_cm2, image_filename=file.filename, initial_threshold=threshold)

@app.route('/update_threshold', methods=['POST'])
def update_threshold():
    data = request.get_json()
    threshold = int(data['threshold'])
    image_filename = data['image_filename']
    app.logger.info(f'Updating threshold to {threshold} for file {image_filename}')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
    
    combined_image_path, _ = process_image(file_path, threshold)
    
    return jsonify({'combined_image': combined_image_path})

@app.route('/uploads/<filename>')
def send_uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/processed/<filename>')
def send_processed_file(filename):
    return send_from_directory(app.config['PROCESSED_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
