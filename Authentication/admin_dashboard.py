# admin_dashboard.py
import streamlit as st
import requests
from datetime import datetime, timedelta

def fetch_user_data(email):
    url = "http://13.201.54.118/admin/user"
    data = {"email": email}
    response = requests.get(url, json=data)
    return response.json()

def fetch_all_user_data():
    url = "http://13.201.54.118/admin/get_all_data"
    response = requests.get(url)
    return response.json()

def delete_user(email):
    url = "http://13.201.54.118/admin/user"
    data = {"email": email}
    response = requests.delete(url, json=data)
    return response.json()

def verify_user(email):
    url = "http://13.201.54.118/admin/verify"
    data = {"email": email}
    response = requests.post(url, json=data)
    return response.json()

def get_users_registered_on_date(selected_date):
    url = "http://13.201.54.118/admin/users_registered_on_date"
    params = {"date": selected_date}
    response = requests.get(url, params=params)
    return response.json()

def get_non_verified_users():
    url = "http://13.201.54.118/admin/get_non_verified_users"
    response = requests.get(url)
    return response.json()

def delete_non_verified_user(email):
    url = "http://13.201.54.118/admin/delete_non_verified_users"
    data = {"email": email}
    response = requests.delete(url, json=data)
    return response.json()

def get_login_logs():
    url = "http://13.201.54.118/admin/get_login_logs"
    response = requests.get(url)

    if response.status_code == 200:
        return response.content
    else:
        return response.json()
    

def delete_previous_logs():
    url = "http://13.201.54.118/admin/delete_previous_logs"
    response = requests.delete(url)
    return response.json()


def fetch_users_in_time_duration(duration):
    url = "http://13.201.54.118/admin/users_in_time_duration"
    params = {"duration": duration}
    response = requests.get(url, params=params)
    return response.json()
    

def main():
    # Center the titles horizontally
    st.markdown("""
        <h1 style='text-align: center; font-size: 4em; text-decoration: underline;'>Admin Dashboard</h1>
        <h2 style='text-align: left;'>Gemini MCQ Expert</h2>
        """, unsafe_allow_html=True)

    # Sidebar for user actions
    st.sidebar.header("Actions")
    selected_action = st.sidebar.selectbox("Select Action", [
        "Fetch User Data",
        "User Registration Statistics",
        "Delete User",
        "Verify User",
        "Users Registered on Date",
        "Manage Non-Verified Users",
        "Download Login Logs"
        
    ])

    if selected_action == "Fetch User Data":
        st.subheader("Fetch User Data")
        email = st.text_input("Enter user email:")
        if st.button("Fetch"):
            user_data = fetch_user_data(email)
            st.json(user_data)

    elif selected_action == "User Registration Statistics":
        st.subheader("Fetch Users in Time Duration")
        selected_duration = st.selectbox("Select Time Duration", ["Last 30 Days", "Last 6 Months", "Last Year", "All Time"])

        if st.button("Fetch Users"):
            # Convert selected duration to timedelta
            if selected_duration == "Last 30 Days":
                duration = timedelta(days=30)
            elif selected_duration == "Last 6 Months":
                duration = timedelta(days=6 * 30)
            elif selected_duration == "Last Year":
                duration = timedelta(days=365)
            else:
                duration = timedelta(days=365*10)
                users_in_duration = fetch_all_user_data()

            # Fetch users based on duration
            if duration:
                end_date = datetime.now()
                start_date = end_date - duration
                users_in_duration = fetch_users_in_time_duration((start_date, end_date))
                st.json(users_in_duration)
            else:
                st.warning("Invalid time duration selected.")

    elif selected_action == "Delete User":
        st.subheader("Delete User")
        email_to_delete = st.text_input("Enter user email:")
        if st.button("Delete"):
            result = delete_user(email_to_delete)
            st.json(result)

    elif selected_action == "Verify User":
        st.subheader("Verify User")
        email_to_verify = st.text_input("Enter user email:")
        if st.button("Verify"):
            result = verify_user(email_to_verify)
            st.json(result)

    elif selected_action == "Users Registered on Date":
        st.subheader("Users Registered on Date")
        selected_date = st.date_input("Select date:")
        if st.button("Fetch"):
            users_on_date = get_users_registered_on_date(selected_date.strftime("%Y-%m-%d"))
            st.json(users_on_date)

    elif selected_action == "Manage Non-Verified Users":
        st.subheader("Manage Non-Verified Users")
        
        # Section to add email and delete users
        st.subheader("Add Email to Delete Non-Verified User")
        email_to_delete_non_verified = st.text_input("Enter user email:")
        if st.button("Delete Non-Verified User"):
            result = delete_non_verified_user(email_to_delete_non_verified)
            st.json(result)


        # Fetch non-verified users
        if st.button("Non verified users"):
            non_verified_users = get_non_verified_users()
            st.json(non_verified_users)

    elif selected_action == "Download Login Logs":
        st.subheader("Download Login Logs")

        if st.button("Get File"):
            logs_content = get_login_logs()
            if logs_content:
                st.download_button(
                    label="Download Log File",
                    data=logs_content,
                    file_name="login_logs.csv",
                    key="download_button"
                )
                st.success("Logs downloaded successfully.")
            else:
                st.json(logs_content)

        st.subheader("Delete previous logs")
        # Add a text field and delete button
        delete_text = st.text_input("Type 'Delete' to enable delete button:")
        delete_button_enabled = delete_text == 'Delete'
    
        
        if st.button("Delete Previous Logs", disabled=not delete_button_enabled):
            if delete_button_enabled:
                result = delete_previous_logs()
                st.json(result)
            else:
                st.warning("Type 'delete' in the text field to enable delete button.")
    


    

if __name__ == "__main__":
    main()
