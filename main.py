from flask import Flask, render_template, request, flash, redirect, url_for, session
from database import getUserData, createNewUser, energy_used, get_hourly_energy_usage, get_user_devices, set_new_budget
from database import add_new_device, remove_old_device

app = Flask(__name__)
app.secret_key = 'database_project'

@app.route('/', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        userData = getUserData(username)

        if userData and username == userData[1] and password == userData[3]: 
            print('Successful login.')

            total_en = energy_used(userData[0])
            user_devices = get_user_devices(userData[0])
            hourly_data = get_hourly_energy_usage(userData[0])

            session['user_id'] = userData[0]
            session['username'] = userData[1]
            session['total_energy'] = total_en
            session['user_devices'] = user_devices
            session['hourly_data'] = hourly_data

            labels = hourly_data['labels']
            values = hourly_data['data']

            username = username.capitalize()
            return render_template('dashboard.html', usr=username, total_energy=total_en, usr_device=user_devices, 
                                   labels=labels, values=values)
        else:
            print(f"Failed login attempt for user: {username}")
            flash("Invalid username or password.")
            
            return redirect(url_for('login_page'))

    return render_template('log_in.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        return "Password Successfully Changed!"

    return render_template('forgot_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            createNewUser([name, email, password])
            return redirect(url_for('login_page'))
        else:
            return "Passwords do not match."
        
    return render_template('register.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    return render_template('dashboard.html')

@app.route('/budget_settings', methods=['GET', 'POST'])
def budget_settings():
    if request.method == 'POST':
        new_budget = request.form.get('budget')

        new_budget = float(new_budget)
        
        if new_budget <= 0:
            flash('Budget can not be zero or negative.')
            return render_template('budget_settings.html')
        else:
            user_id = session.get('user_id')
            set_new_budget(user_id, new_budget)
            flash('New Budget Successfully Set.')
            return render_template('budget_settings.html')
    return render_template('budget_settings.html')

@app.route('/manage_devices', methods=['GET', 'POST'])
def manage_devices():
    user_id = session.get('user_id')
    devices = get_user_devices(user_id) 
    return render_template('manage_devices.html', user_devices=devices)

@app.route('/add_device', methods=['POST'])
def add_device():
    device_name = request.form.get('device_name')
    room_name = request.form.get('room_name')
    max_wattage = request.form.get('max_wattage')

    userid = session.get('user_id')

    add_new_device(userid, device_name, room_name, max_wattage)
    flash('Device added successfully!')
    return render_template('manage_devices.html')

@app.route('/remove_device', methods=['POST'])
def remove_device():
    userid = session.get('user_id')
    remove_old_device(userid)
    flash('Device removed.')
    return render_template('manage_devices.html')

@app.route('/logout')
def logout():
    session.clear() 
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)