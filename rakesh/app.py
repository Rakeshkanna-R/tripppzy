# pip install streamlit requests sqlite3 langchain-google-genai langchain-core
# streamlit run app.py

import streamlit as st
import base64
import os
import requests
import sqlite3
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

os.environ["GOOGLE_API_KEY"] = "AIzaSyDeCfka3goQtaqdQFQ6IDW2qkdneps-Otw"
weather_api_key = "d356b277d7ff8fe30aa4971bfa6b7f92"

# Set page configuration
st.set_page_config(page_title="Travel Planner", page_icon=":earth_africa:", layout="wide")

st.markdown("""
<style>
@keyframes fly {
    from { transform: translateX(-100%); }
    to { transform: translateX(1000%); }
}
.airplane {
    position: absolute;
    top: 50%;
    left: 0;
    animation: fly 5s linear infinite;
    font-size: 200%; /* Increase this value to make the airplane larger */
}
</style>
<div class="airplane">✈️ 🪂 🛩️</div>
""", unsafe_allow_html=True)

st.balloons()
# st.snow()



# Function to encode the image to Base64
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        encoded_string = base64.b64encode(img_file.read()).decode()
    return encoded_string

# Path to the image file
image_path = r"11f105bd12788fd5a72febe7585fecab.jpg"
encoded_image = get_base64_image(image_path)

# # CSS for the background image and styling
# page_bg_img = f"""
# <style>
# [data-testid="stAppViewContainer"] {{
#     background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
#                 url("data:image/jpg;base64,{encoded_image}");
#     background-size: cover;
#     background-position: center;
#     background-repeat: no-repeat;
#     background-attachment: fixed;
# }}

# [data-testid="stSidebar"] {{
#     background-color: rgba(255, 255, 255, 0.9); /* Sidebar transparency */
#     color: black; /* Sidebar text color */
# }}

# h1, h2, h3, h4, h5, h6, label {{
#     color: black !important; /* Ensure text visibility */
# }}

# .stButton > button {{
#     background-color: #4CAF50; /* Green */
#     color: white; 
#     border-radius: 5px;
# }}

# .stButton > button:hover {{
#     background-color: #45a049; /* Darker green */
# }}
# </style>
# """

# CSS for the background image and styling
page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background: url("data:image/jpg;base64,{encoded_image}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: black;
}}

[data-testid="stSidebar"] {{
    background-color: rgba(255, 255, 255, 0.9); /* Sidebar transparency */
    color: black; /* Sidebar text color */
}}

h1, h2, h3, h4, h5, h6, label {{
    color: black !important; /* Ensure text visibility */
}}

.stButton > button {{
    background-color: #4CAF50; /* Green */
    color: white; 
    border-radius: 5px;
}}

.stButton > button:hover {{
    background-color: #45a049; /* Darker green */
}}

/* Custom styles for success and error messages */
[data-testid="stAlert"] {{
    background-color: rgba(76, 175, 80, 0.8); /* Light green with reduced transparency */
    color: white; /* Text color */
}}

[data-testid="stException"] {{
    background-color: rgba(244, 67, 54, 0.8); /* Light red with reduced transparency */
    color: white; /* Text color */
}}

/* Custom styles for specific Markdown container */
.custom-markdown {{
    margin: 10px; /* Add margin if needed */
    padding: 20px; /* Add padding for better spacing */
    background-color: rgba(255, 255, 255, 0.8); /* White with reduced transparency */
    backdrop-filter: blur(10px); /* Add blur effect for glass effect */
    border-radius: 10px; /* Optional: rounded corners */
    color: black; /* Text color */
}}



</style>
"""


# Apply the CSS
st.markdown(page_bg_img, unsafe_allow_html=True)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY,
            username TEXT,
            city TEXT,
            temperature REAL,
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Function to fetch weather information
def get_weather(city):
    api_key = weather_api_key  # Replace with your actual OpenWeatherMap API key
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error for bad responses (4xx or 5xx)
        data = response.json()
        
        # Extract relevant information
        weather_info = {
            "city": data["name"],
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"]
        }
        return weather_info
    except requests.exceptions.HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")  # Specific HTTP error
    except requests.exceptions.ConnectionError:
        st.error("Connection error: Please check your internet connection.")
    except requests.exceptions.Timeout:
        st.error("Timeout error: The request took too long to respond.")
    except requests.exceptions.RequestException as err:
        st.error(f"An error occurred: {err}")  # General error handling
    except KeyError:
        st.error("Could not retrieve weather information for this location.")
    
    return None

# Function to save interaction to the database
def save_interaction(username, city, temperature, description):
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO interactions (username, city, temperature, description) 
        VALUES (?, ?, ?, ?)
    ''', (username, city, temperature, description))
    
    conn.commit()
    conn.close()

# Define the function to generate the travel plan using AI
def generate_response(destination, number_of_days, budget):
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant that plans trips based on the user's destination, number of days, and budget."
                "and here the google map location link <<https://www.google.com/maps/place/>> add the locations to this link and provide location link to user",
            ),
            (
                "human",
                f"Plan my trip to {destination}. I want to stay for {number_of_days} days and my budget is {budget}. "
                "Please suggest accommodation, food options, transportation tips, activities to do, and places to visit."
            ),
        ]
    )
    
    chain = prompt | llm
    ai_response = chain.invoke({"destination": destination, "number_of_days": number_of_days, "budget": budget})
    
    return ai_response.content

# Initialize session state attributes if they don't exist
if 'authenticated' not in st.session_state:
   st.session_state.authenticated = False

if 'username' not in st.session_state:
   st.session_state.username = ""

if 'trip_history' not in st.session_state:
   st.session_state.trip_history = []

if 'feedback' not in st.session_state:
   st.session_state.feedback = []

# Authentication functions
def login(username, password):
   conn = sqlite3.connect('user_data.db')
   c = conn.cursor()
   
   c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
   
   user = c.fetchone()
   
   conn.close()
   
   if user:
       st.session_state.authenticated = True
       st.session_state.username = username
       st.success("Login successful!")
   else:
       st.error("Invalid username or password.")

def signup(username, password):
   conn = sqlite3.connect('user_data.db')
   
   try:
       c = conn.cursor()
       c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
       
       conn.commit()
       
       st.success("Signup successful! Please log in.")
       
   except sqlite3.IntegrityError:
       st.error("Username already exists. Please choose a different one.")
   
   finally:
       conn.close()

# Profile management functions
def update_profile(new_username):
   if new_username and new_username != st.session_state.username:
       conn = sqlite3.connect('user_data.db')
       c = conn.cursor()
            
       c.execute('UPDATE users SET username=? WHERE username=?', (new_username, st.session_state.username))
            
       conn.commit()
            
       st.session_state.username = new_username
            
       conn.close()
            
       st.success("Username updated successfully!")

# Feedback submission function
def submit_feedback(feedback_text):
   if feedback_text:
       st.session_state.feedback.append(feedback_text)
       
       # Save feedback to database (optional)
       conn = sqlite3.connect('user_data.db')
       
       c = conn.cursor()
       
       c.execute('INSERT INTO interactions (username, city) VALUES (?, ?)', (st.session_state.username, feedback_text))
       
       conn.commit()
       
       conn.close()
       
       st.success("Thank you for your feedback!")

# Login and Signup page layout
if not st.session_state.authenticated:
   st.sidebar.title("Login / Signup")
   
   option = st.sidebar.selectbox("Choose option", ["Login", "Signup"])

   if option == "Login":
       st.sidebar.subheader("Login")
       
       username = st.sidebar.text_input("Username")
       
       password = st.sidebar.text_input("Password", type="password")
       
       if st.sidebar.button("Login"):
           login(username, password)

   elif option == "Signup":
       st.sidebar.subheader("Signup")
       
       new_username = st.sidebar.text_input("Create Username")
       
       new_password = st.sidebar.text_input("Create Password", type="password")
       
       if st.sidebar.button("Signup"):
           signup(new_username, new_password)
else:
   # User Profile Management Section
   with st.sidebar.expander("Profile Management"):
       new_username = st.text_input("Update Username", value=st.session_state.username)
       
       if st.button("Update Profile"):
           update_profile(new_username)

   # Trip History Section
   with st.sidebar.expander("Trip History"):
       if len(st.session_state.trip_history) > 0:
           for idx, trip in enumerate(st.session_state.trip_history):
               st.write(f"{idx + 1}. {trip}")
       else:
           st.write("No trips planned yet.")

   # Feedback Section...
   with st.sidebar.expander("Feedback"):
       feedback_text = st.text_area("Share your feedback about the app:")
       
       if st.button("Submit Feedback"):
           submit_feedback(feedback_text)

   # Logout Option
   if st.sidebar.button("Logout"):
       st.session_state.authenticated = False
       st.session_state.username = ""
       st.experimental_rerun()

# Travel planner UI for authenticated users
if st.session_state.authenticated:
   st.title("Your Personalized Trip Planner")
   
   destination = st.text_input("Enter your travel destination:")
   
   number_of_days = st.number_input("Enter number of days for the trip:", min_value=1)
   
   budget = st.text_input("Enter your budget (e.g., $2000):")

   # Fetch Weather Information Button
   if destination and number_of_days and budget and st.button("Get Weather Info"):
       weather_info = get_weather(destination)
       
       if weather_info:
           temp = weather_info["temperature"]
           desc = weather_info["description"]
           city = weather_info["city"]
           humidity = weather_info["humidity"]
           wind_speed = weather_info["wind_speed"]
           
           weather_details = (
               f"The current temperature in {city} is {temp}°C with {desc}. "
               f"Humidity: {humidity}% | Wind Speed: {wind_speed} m/s."
           )
           
           # Display weather information successfully retrieved.
           st.success(weather_details)
           
           # Save interaction to the database.
           save_interaction(st.session_state.username, city, temp, desc)
           
       else:
           # Display error message if weather info could not be retrieved.
           st.error("Could not retrieve weather information.")

   if destination and number_of_days and budget and st.button("Generate Travel Plan"):
       with st.spinner("Generating travel plan..."):
           response_content = generate_response(destination, number_of_days, budget)
           
           # Save trip to history for later reference.
           trip_details = f"{destination}, {number_of_days} days, Budget: {budget}"
           
           if trip_details not in st.session_state.trip_history:
               st.session_state.trip_history.append(trip_details)
               
           # Display generated travel plan from AI response.
           st.markdown(f'<div class="custom-markdown">{response_content}</div>', unsafe_allow_html=True)

else:
   # Prompt for login if not authenticated.
   st.title("Please log in to access the Trip Planner.")
