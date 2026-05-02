from flask import Flask, render_template, request, flash, redirect, url_for
from database import getUserData

app = Flask(__name__)
app.secret_key = 'database_project'

@app.route('/', methods=['GET', 'POST'])
def login_page():
    error = None

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        userData = getUserData(username)

        if userData and username == userData[1] and password == userData[2]: 
            print('Successful login.')
            return "Login Successful! Welcome to the Dashboard." 
        else:
            print(f"Failed login attempt for user: {username}")
            flash("Invalid username or password.")
            
            return redirect(url_for('login_page'))

    return render_template('log_in.html',error=error)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        # The user clicked the "Log In" button!
        password = request.form.get('password')

        return "Password Successfully Changed!"

    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            return "User successfully created."
        else:
            return "Passwords do not match."
        
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)