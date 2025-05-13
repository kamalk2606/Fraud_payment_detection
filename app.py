from flask import Flask, render_template, request, redirect, url_for, session, flash
import numpy as np
import pickle
import requests
import os
import json
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secret key for session management

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
API_ENDPOINT = "https://aavzy9x555.execute-api.us-east-1.amazonaws.com/PS-2/PS2-API-MODEL"

# User model for database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

# Create database tables
with app.app_context():
    db.create_all()

# Load the trained model
model = pickle.load(open("static/model.pkl", "rb"))

@app.route('/')
def home():
    if 'user_id' in session:
        return render_template('index.html')
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if username or email already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            flash('Username or email already exists')
        else:
            # Create new user with hashed password
            hashed_password = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created successfully! Please log in.')
            return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

# @app.route('/predict', methods=['POST'])
# def predict():
#     # Check if user is logged in
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
        
#     # Get input values from the form
#     type = request.form['type']
#     step = float(request.form['step'])
#     amount = float(request.form['amount'])
#     oldbalanceOrg = float(request.form['oldbalanceOrg'])
#     newbalanceOrig = float(request.form['newbalanceOrig'])
#     oldbalanceDest = float(request.form['oldbalanceDest'])
#     newbalanceDest = float(request.form['newbalanceDest'])

#     # Initialize transaction type flags
#     cash_out = 1 if type == "CASH_OUT" else 0
#     debit = 1 if type == "DEBIT" else 0
#     payment = 1 if type == "PAYMENT" else 0
#     transfer = 1 if type == "TRANSFER" else 0

#     # Create input array for prediction
#     input_array = np.array([[
#         step, amount, oldbalanceOrg, newbalanceOrig,
#         oldbalanceDest, newbalanceDest, cash_out,
#         debit, payment, transfer
#     ]])

#     # Make prediction using the loaded model
#     prediction = model.predict(input_array)

#     # Extract the predicted output value
#     output = prediction[0]
    

#     return render_template('index.html', prediction=output)


@app.route('/predict', methods=['POST'])
def predict():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    # Get input values from the form
    type = request.form['type']
    step = float(request.form['step'])
    amount = float(request.form['amount'])
    oldbalanceOrg = float(request.form['oldbalanceOrg'])
    newbalanceOrig = float(request.form['newbalanceOrig'])
    oldbalanceDest = float(request.form['oldbalanceDest'])
    newbalanceDest = float(request.form['newbalanceDest'])

    # Initialize transaction type flags
    type_CASH_IN = 1 if type == "CASH_IN" else 0
    type_CASH_OUT = 1 if type == "CASH_OUT" else 0
    type_DEBIT = 1 if type == "DEBIT" else 0
    type_PAYMENT = 1 if type == "PAYMENT" else 0
    type_TRANSFER = 1 if type == "TRANSFER" else 0
    
    # Flag for fraud (assuming this is always 0 for new transactions)
    isFlaggedFraud = 0
    
    # Format the input data for the API according to the expected order:
    # step,amount,oldbalanceOrg,newbalanceOrig,oldbalanceDest,newbalanceDest,isFlaggedFraud,type_CASH_IN,type_CASH_OUT,type_DEBIT,type_PAYMENT,type_TRANSFER
    input_data = f"{step},{amount},{oldbalanceOrg},{newbalanceOrig},{oldbalanceDest},{newbalanceDest},{isFlaggedFraud},{type_CASH_IN},{type_CASH_OUT},{type_DEBIT},{type_PAYMENT},{type_TRANSFER}"
    
    # Prepare the API request payload
    payload = {
        "data": input_data
    }
    
    try:
        # Make the API request
        response = requests.post(API_ENDPOINT, json=payload)
        print(payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            api_response = response.json()
            print(api_response)
            
            # Extract the result from the API response
            if isinstance(api_response, dict) and "body" in api_response:
                # Parse the body which is a JSON string
                body = json.loads(api_response["body"]) if isinstance(api_response["body"], str) else api_response["body"]
                
                # Get the probability score from the result field
                if "result" in body:
                    probability = float(body["result"])
                    
                    # Determine if it's fraud based on a threshold of 0.5
                    is_fraud = probability >= 0.5
                    
                    # Create a simple output message
                    if is_fraud:
                        output = "FRAUD DETECTED: This transaction appears to be fraudulent."
                    else:
                        output = "NOT FRAUD: This transaction appears to be legitimate."
                    
                    # Add the probability for reference
                    # output += f" (Probability score: {probability})"
                else:
                    output = "Error: No result field in API response body"
            else:
                output = str(api_response)
        else:
            output = f"Error: API request failed with status code {response.status_code}"
    
    except Exception as e:
        output = f"Error: {str(e)}"

    return render_template('index.html', prediction=output)

if __name__ == '__main__':
    app.run(debug=True)