# app.py
from flask import Flask, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
from PIL import Image


UPLOAD_FOLDER = 'file_loc'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def allowed_files(filename):
     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



from dotenv import load_dotenv

load_dotenv() # Loads all the environment variables from .env

import streamlit as st
import os

import google.generativeai as genai 

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))






## Function to load gemini pro vision
model = genai.GenerativeModel('gemini-pro-vision')


# Function returns response from gemini
def get_gemini_response(input, image, prompt):
    response = model.generate_content([input, image, prompt])
    return response.text



def input_image_details(uploaded_file):
    #Read the file into bytes
        bytes_data = uploaded_file.read()

        image_parts = [
            {
                "mime_type": uploaded_file.type, # Get the mime type
                "data": bytes_data
            }
        ]

        return image_parts




input_prompt = """
You are an expert in answering MCQ questions. We will upload an image of mcq question(s) 
and you will have to answer the correct option based upon the question number provided.
Try to be as accurate as possible. 
Respond "Image not an MCQ" if MCQ question not provided.
"""






@app.route('/process', methods=['POST'])
def process_request():


    # Checking if image in request files or not
    if 'image' not in request.files:
        return jsonify({'message': 'media not provided'})


    # Get image data from the request
    uploaded_file = request.files['image']

    # Get text data from the request
    text = request.form['text']

    if uploaded_file.filename == '':
        return jsonify({'message':'No file selected'})
    


    if uploaded_file and allowed_files(uploaded_file.filename):
        filename = secure_filename(uploaded_file.filename)
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)


    try:
        img = Image.open(img_path)
    except Exception as e:
        return jsonify({'error': f'Error opening image: {str(e)}'})

    # image_data = input_image_details(uploaded_file)

    response_a = get_gemini_response(input_prompt, img, text)

    if(text):
        response = {'message': response_a}


    # Use `jsonify` to convert the dictionary to a JSON response
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)

