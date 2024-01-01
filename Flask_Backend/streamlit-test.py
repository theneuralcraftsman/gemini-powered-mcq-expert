# streamlit_app.py
import streamlit as st
import requests


def main():
    st.title("Flask and Streamlit App")

    # File uploader for image
    uploaded_image = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"])

    # Text input
    text_input = st.text_input("Enter Text")

    if st.button("Submit"):
        # if uploaded_image is not None:
            
        # Send image and text to Flask server
        files = {'image': uploaded_image}
        data = {'text': text_input}
        response = requests.post('http://127.0.0.1:5000/process', files=files, data=data)

        # Display the response from Flask
        st.success(response.json()['message'])
        # else:
        #     st.warning("Please upload an image")

if __name__ == "__main__":
    main()
