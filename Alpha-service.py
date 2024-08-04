from flask import Flask, render_template, jsonify, request
import subprocess
import re

app = Flask(__name__)

CONFIG_FILE = '/root/PROJECT-3-K/service-list.conf'

def read_services_from_file():
    """Read the list of services from the configuration file."""
    with open(CONFIG_FILE, 'r') as file:
        lines = file.readlines()
    # Extract services from the file
    services = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('#'):
            if line.startswith('services ='):
                # Remove 'services =' and split by commas
                services = line.split('=', 1)[1].strip().strip('[]').replace('"', '').split(',')
                services = [s.strip() for s in services]
    return services

services = read_services_from_file()

def get_service_details(service):
    """Get detailed information about a service using systemctl."""
    try:
        result = subprocess.run(['systemctl', 'status', service], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        status_lines = result.stdout.splitlines()
        
        # Extract status information from the output
        status_info = {
            'status': 'unknown',
            'main_pid': 'N/A',
            'active_since': 'N/A',
            'last_active_since': 'N/A'
        }
        
        for line in status_lines:
            if 'Active:' in line:
                status_info['status'] = line.split(':', 1)[1].strip()
            if 'Main PID:' in line:
                status_info['main_pid'] = line.split(':', 1)[1].strip()
            if 'since' in line and 'Active:' in line:
                status_info['active_since'] = line.split('since', 1)[1].strip()
            if 'Active:' in line and 'inactive' in line:
                match = re.search(r'\(dead\)\s+since\s+(.+)', line)
                if match:
                    status_info['last_active_since'] = match.group(1).strip()
                
        return status_info
    except subprocess.CalledProcessError:
        return {'status': 'error', 'main_pid': 'N/A', 'active_since': 'N/A', 'last_active_since': 'N/A'}

def manage_service(action, service):
    """Manage the service (start, stop, restart) using systemctl."""
    subprocess.run(['sudo', 'systemctl', action, service], check=True)

@app.route('/')
def index():
    """Render the main page."""
    return render_template('alphaservice.html')

@app.route('/status')
def status():
    """Return the status of all services as JSON."""
    service_details = {}
    for service in services:
        details = get_service_details(service)
        service_details[service] = details
    return jsonify(service_details)

@app.route('/manage', methods=['POST'])
def manage():
    """Handle service management requests (start, stop, restart)."""
    data = request.json
    action = data.get('action')
    service = data.get('service')

    if action in ['start', 'stop', 'restart'] and service in services:
        try:
            manage_service(action, service)
            return jsonify({'status': 'success'})
        except subprocess.CalledProcessError:
            return jsonify({'status': 'error', 'message': 'Failed to manage service'}), 500
    return jsonify({'status': 'error', 'message': 'Invalid action or service'}), 400

if __name__ == '__main__':
    app.run(debug=True)

