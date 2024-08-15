from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import os
import subprocess
import zipfile
from datetime import datetime
import configparser
import psutil
import humanize
import logging
import requests
import socket

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Change this to a secure secret key

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Read usernames and passwords from credentials.conf
config = configparser.ConfigParser()
config.read('credentials.conf')
users = dict(config['USERS'])

# Geo-location
def get_location(ip_address=None):
    url = f"https://ipinfo.io/{ip_address}/json" if ip_address else "https://ipinfo.io/json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error getting location: {e}")
        return {}

def get_network_interfaces():
    interfaces = psutil.net_if_addrs()
    interface_info = {}
    for iface, addrs in interfaces.items():
        interface_info[iface] = []
        for addr in addrs:
            if addr.family == socket.AF_INET:
                interface_info[iface].append(addr.address)
    return interface_info

# Function to get running services
def get_running_services():
    try:
        output = subprocess.check_output(['systemctl', 'list-units', '--type=service', '--state=running']).decode()
        services = []
        for line in output.split('\n')[1:]:
            if line.strip():
                parts = line.split()
                services.append({
                    'service_name': parts[0],
                    'active_pid': parts[1],
                    'status': parts[2],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
        return services
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting running services: {e}")
        return []

# Function to get port information
def get_port_information():
    try:
        output = subprocess.check_output(['netstat', '-na']).decode()
        lines = output.split('\n')
        ports = []
        for line in lines:
            parts = line.split()
            if len(parts) >= 4 and parts[0] in ['tcp', 'udp'] and ':' in parts[3]:
                protocol = parts[0]
                local_address = parts[3]
                local_ip, local_port = local_address.split(':')
                remote_address = parts[4] if len(parts) >= 5 else None
                if remote_address:
                    remote_ip, remote_port = remote_address.split(':')
                else:
                    remote_ip, remote_port = None, None
                state = parts[5] if len(parts) >= 6 else ""
                ports.append({
                    'protocol': protocol,
                    'local_ip': local_ip,
                    'local_port': local_port,
                    'remote_ip': remote_ip,
                    'remote_port': remote_port,
                    'state': state
                })
        return ports
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting port information: {e}")
        return []

# Function to execute terminal commands
def execute_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode()
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command '{command}': {e.output.decode()}")
        return e.output.decode()
    except Exception as e:
        logger.error(f"Unexpected error executing command '{command}': {str(e)}")
        return str(e)

# Function to collect last logins
def collect_last_logins(output_directory):
    os.makedirs(output_directory, exist_ok=True)

    result = subprocess.run(['last', '-F'], capture_output=True, text=True)
    login_output = result.stdout

    today_date = datetime.now().strftime('%d-%m-%Y')
    log_filename = f'last_logins-{today_date}.txt'
    log_path = os.path.join(output_directory, log_filename)
    with open(log_path, 'w') as log_file:
        log_file.write(login_output)

    zip_filename = f'last_logins-{today_date}.zip'
    zip_path = os.path.join(output_directory, zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zip_file:
        zip_file.write(log_path, arcname=log_filename)

    logins = []
    for line in login_output.splitlines():
        if line.strip():
            parts = line.split()
            if len(parts) >= 10:
                user = parts[0]
                terminal = parts[1]
                session_type = parts[2]
                login_time = ' '.join(parts[3:8])
                status = ' '.join(parts[8:])
                logins.append((user, terminal, session_type, login_time, status))
            else:
                logins.append((' '.join(parts[:-4]), '', '', ' '.join(parts[-4:-1]), parts[-1]))

    return logins, zip_filename

# Function to list files and directories
def list_files(dir_path):
    try:
        files = []
        if os.path.isdir(dir_path):
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                is_dir = os.path.isdir(file_path)
                
                files.append({
                    'name': file_name,
                    'is_dir': is_dir
                })
        current_path = os.path.abspath(dir_path)
        return {'files': files, 'current_path': current_path}
    except Exception as e:
        logger.error(f"Error listing files in directory {dir_path}: {e}")
        return {'error': str(e)}

# Function to open a file and read its content
def open_file(file_path):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
        return {'content': content}
    except Exception as e:
        logger.error(f"Error opening file {file_path}: {e}")
        return {'error': str(e)}

# Function to save content to a file
def save_file(file_path, content):
    try:
        with open(file_path, 'w') as file:
            file.write(content)
        return {'message': 'File saved successfully.'}
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {e}")
        return {'error': str(e)}

# Routes

@app.route('/')
def login_redirect():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', title='Login', message='Invalid username or password')
    return render_template('login.html', title='Login')

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('index-pro.html', title='Home')

@app.route('/geo')
def geo():
    location_info = get_location()
    loc = location_info.get('loc', '0,0').split(',')
    latitude = loc[0]
    longitude = loc[1]
    network_interfaces = get_network_interfaces()
    return render_template('geo.html', title='Geo Location', location=location_info, latitude=latitude, longitude=longitude, interfaces=network_interfaces)

@app.route('/refresh_location')
def refresh_location():
    location_info = get_location()
    return jsonify(location_info)

@app.route('/network_interfaces')
def network_interfaces():
    interfaces = get_network_interfaces()
    return jsonify(interfaces)

@app.route('/running_services')
def running_services():
    if 'username' not in session:
        return redirect(url_for('login'))
    services = get_running_services()
    return render_template('service_info.html', title='Running Services', services=services)

@app.route('/restart/<service_name>', methods=['POST'])
def restart_service(service_name):
    try:
        subprocess.run(['systemctl', 'restart', service_name], check=True)
        return redirect(url_for('home'))
    except subprocess.CalledProcessError as e:
        logger.error(f"Error restarting service '{service_name}': {e}")
        return "Error restarting service", 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/resource_information')
def resource_information():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    disk_usage = psutil.disk_usage('/')
    total_disk_space = humanize.naturalsize(disk_usage.total)
    used_disk_space = humanize.naturalsize(disk_usage.used)
    used_disk_space_percent = disk_usage.percent

    virtual_memory = psutil.virtual_memory()
    total_memory = humanize.naturalsize(virtual_memory.total)
    used_memory = humanize.naturalsize(virtual_memory.used)
    used_memory_percent = virtual_memory.percent

    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    return render_template('system_info.html', title='Resource Information', 
                           total_disk_space=total_disk_space, used_disk_space=used_disk_space, 
                           used_disk_space_percent=used_disk_space_percent, total_memory=total_memory, 
                           used_memory=used_memory, used_memory_percent=used_memory_percent, uptime=uptime)

@app.route('/data')
def get_data():
    disk_usage = psutil.disk_usage('/')
    memory_usage = psutil.virtual_memory()

    data = {
        'disk': {
            'total': f"{disk_usage.total / (1024 ** 3):.2f} GB",
            'used': f"{disk_usage.used / (1024 ** 3):.2f} GB",
            'free': f"{disk_usage.free / (1024 ** 3):.2f} GB"
        },
        'memory': {
            'total': f"{memory_usage.total / (1024 ** 3):.2f} GB",
            'used': f"{memory_usage.used / (1024 ** 3):.2f} GB",
            'free': f"{memory_usage.available / (1024 ** 3):.2f} GB"
        }
    }

    return jsonify(data)

@app.route('/port_information')
def port_information():
    if 'username' not in session:
        return redirect(url_for('login'))
    port_info = get_port_information()
    return render_template('port_info.html', title='Port Information', port_info=port_info)

@app.route('/terminal')
def terminal():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('terminal.html', title='Terminal')

@app.route('/execute_command', methods=['POST'])
def execute_terminal_command():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    command = request.form['command']
    output = execute_command(command)
    
    return render_template('terminal.html', title='Terminal', command=command, output=output)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', title='Dashboard')

@app.route('/last_logins')
def last_logins():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    output_directory = '/home/Last-logins'
    logins, zip_filename = collect_last_logins(output_directory)
    return render_template('last_logins.html', logins=logins, zip_filename=zip_filename)

@app.route('/download_last_logins')
def download_last_logins():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    output_directory = '/home/Last-logins'
    _, zip_filename = collect_last_logins(output_directory)
    zip_path = os.path.join(output_directory, zip_filename)
    return send_file(zip_path, as_attachment=True)

# File manager routes

@app.route('/file_manager')
def file_manager():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('file_manager.html')

@app.route('/list', methods=['POST'])
def list_files_route():
    dir_path = request.json.get('dir_path', '/')
    # Validate directory path here if necessary
    return jsonify(list_files(dir_path))

@app.route('/open', methods=['POST'])
def open_file_route():
    file_path = request.json.get('file_path', '')
    # Validate file path here if necessary
    return jsonify(open_file(file_path))

@app.route('/save', methods=['POST'])
def save_file_route():
    file_path = request.form.get('file_path', '')
    content = request.form.get('content', '')
    # Validate file path here if necessary
    return jsonify(save_file(file_path, content))

if __name__ == '__main__':
    app.run(debug=True)

