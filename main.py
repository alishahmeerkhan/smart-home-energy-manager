from flask import Flask, render_template, request
from database import getUserData

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        # The user clicked the "Log In" button!
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Here is where you will eventually call your database function
        print(f"Attempting to log in user: {username}")
        return "Form submitted successfully!"
        
    # If it's a GET request, just show the login page
    return render_template('log_in.html')

if __name__ == '__main__':
    app.run(debug=True)