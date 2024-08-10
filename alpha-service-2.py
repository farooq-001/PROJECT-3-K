import subprocess
import re
import logging
import psutil
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

CONFIG_FILE = '/root/PROJECT-3-K/service-list.conf'

# Configure logging
logging.basicConfig(filename='service_manager.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def read_services_from_file():
    """Read the list of services from the configuration file."""
    try:
        with open(CONFIG_FILE, 'r') as file:
            lines = file.readlines()
        services = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and line.startswith('services ='):
                services = line.split('=', 1)[1].strip().strip('[]').replace('"', '').split(',')
                services = [s.strip() for s in services]
                break
        return services
    except IOError as e:
        logging.error(f"Failed to read configuration file: {e}")
        return []

def write_services_to_file(services):
    """Write the list of services to the configuration file."""
    try:
        with open(CONFIG_FILE, 'w') as file:
            file.write('services = [\n')
            for service in services:
                file.write(f'    "{service}",\n')
            file.write(']\n')
    except IOError as e:
        logging.error(f"Failed to write configuration file: {e}")

services = read_services_from_file()

def get_service_details(service):
    """Get detailed information about a service using systemctl."""
    try:
        result = subprocess.run(['systemctl', 'status', service], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        status_lines = result.stdout.splitlines()
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
        logging.error(f"Failed to get status for service: {service}")
        return {'status': 'error', 'main_pid': 'N/A', 'active_since': 'N/A', 'last_active_since': 'N/A'}

def manage_service(action, service):
    """Manage the service (start, stop, restart) using systemctl."""
    try:
        subprocess.run(['sudo', 'systemctl', action, service], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to {action} service {service}: {e}")
        raise

@app.route('/')
def index():
    """Render the main page."""
                'used': memory_info.used / (1024 ** 3),
    return render_template('alpha-service-2.html')

@app.route('/status')
def status():
    """Return the status of all services as JSON."""
    service_details = {service: get_service_details(service) for service in services}
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
            logging.info(f"Successfully performed {action} on service: {service}")
            return jsonify({'status': 'success'})
        except subprocess.CalledProcessError:
            return jsonify({'status': 'error', 'message': 'Failed to manage service'}), 500
    return jsonify({'status': 'error', 'message': 'Invalid action or service'}), 400

@app.route('/add_service', methods=['POST'])
def add_service():
    """Handle requests to add a new service."""
    data = request.json
    new_service = data.get('service')
    if new_service and new_service not in services:
        services.append(new_service)
        write_services_to_file(services)
        logging.info(f"Added new service: {new_service}")
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Service already exists or invalid service name'}), 400

@app.route('/remove_service', methods=['POST'])
def remove_service():
    """Handle requests to remove a service."""
    data = request.json
    service_to_remove = data.get('service')
    if service_to_remove in services:
        services.remove(service_to_remove)
        write_services_to_file(services)
        logging.info(f"Removed service: {service_to_remove}")
        return jsonify({'status': 'success'})
    return jsonify({'status': 'error', 'message': 'Service not found'}), 400

@app.route('/vitals')
def vitals():
    """Return system vitals as JSON."""
    try:
        # Gather system information
        cpu_perc = psutil.cpu_percent(interval=1, percpu=True)  # Get per-core CPU usage
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')

        # Debugging print statements (remove or replace with logging if needed)
        print(f"CPU Percentages: {cpu_perc}")
        print(f"Memory Info: {memory_info}")
        print(f"Disk Info: {disk_info}")

        # Format data
        data = {
            'Disk': {
                'total': disk_info.total / (1024 ** 3),  # Convert bytes to GB
                'free': disk_info.free / (1024 ** 3),
                'used': disk_info.used / (1024 ** 3),
                'percentage': disk_info.percent
            },
            'Memory': {
                'total': memory_info.total / (1024 ** 3),  # Convert bytes to GB
                'free': memory_info.free / (1024 ** 3),
                'used': memory_info.used / (1024 ** 3),
                'percentage': memory_info.percent
            },
            'CPU': {
                'total_cores': len(cpu_perc),
                'free': 'N/A',
                'used': 'N/A',
                'percentage': sum(cpu_perc) / len(cpu_perc) if cpu_perc else 'N/A'  # Average CPU usage percentage
            }
        }

        return jsonify(data)
    except Exception as e:
        # Log the exception for debugging
        logging.error(f"Failed to retrieve system vitals: {e}")
        return jsonify({'error': str(e)}), 500



if __name__ == '__main__':
    app.run(debug=True)
