import socket
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Simulated threat intelligence data
threat_intelligence = [
    {'ip': '192.168.1.10', 'threat': 'Suspicious IP'},
    {'ip': '10.0.0.1', 'threat': 'Known Malicious IP'},
    {'port': 22, 'threat': 'Commonly Exploited Port'},
    {'port': 3306, 'threat': 'Database Vulnerability'},
]

# Function to scan open ports with protocol detection
def scan_ports():
    common_ports = {
        21: 'FTP',
        22: 'SSH',
        23: 'Telnet',
        25: 'SMTP',
        53: 'DNS',
        80: 'HTTP',
        110: 'POP3',
        143: 'IMAP',
        443: 'HTTPS',
        3306: 'MySQL',
        3389: 'RDP',
    }
    open_ports = []
    for port in range(1, 65535):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        if result == 0:
            protocol = common_ports.get(port, 'Unknown')
            open_ports.append({'port': port, 'protocol': protocol})
        sock.close()
    return open_ports

# Sample firewall rules (for demonstration)
firewall_rules = [
    {'rule_id': 1, 'type': 'firewall', 'protocol': 'TCP', 'port': 80, 'action': 'ALLOW'},
    {'rule_id': 2, 'type': 'firewall', 'protocol': 'UDP', 'port': 53, 'action': 'ALLOW'},
    {'rule_id': 3, 'type': 'port_forward', 'protocol': 'TCP', 'source_port': 8080, 'source_ip': '192.168.1.10', 'dest_ip': '10.0.0.1', 'dest_port': 80},
]

# Sample system vulnerabilities (for demonstration)
system_vulnerabilities = [
    {'id': 1, 'severity': 'High', 'description': 'Open port 22 (SSH) detected'},
    {'id': 2, 'severity': 'Medium', 'description': 'Open port 3306 (MySQL) detected'},
]

# Function to generate the next rule_id
def get_next_rule_id():
    return max(rule['rule_id'] for rule in firewall_rules) + 1 if firewall_rules else 1

# Function to check for vulnerabilities based on firewall rules and threat intelligence
def check_vulnerabilities():
    vulnerabilities = []
    for rule in firewall_rules:
        if 'source_ip' in rule:
            threat = next((item['threat'] for item in threat_intelligence if item.get('ip') == rule['source_ip']), None)
            if threat:
                vulnerabilities.append({'severity': 'High', 'description': f'Threat intelligence detected: {threat} for source IP {rule["source_ip"]}'})
        if 'dest_ip' in rule:
            threat = next((item['threat'] for item in threat_intelligence if item.get('ip') == rule['dest_ip']), None)
            if threat:
                vulnerabilities.append({'severity': 'High', 'description': f'Threat intelligence detected: {threat} for destination IP {rule["dest_ip"]}'})
        if 'port' in rule:
            threat = next((item['threat'] for item in threat_intelligence if item.get('port') == rule['port']), None)
            if threat:
                vulnerabilities.append({'severity': 'Medium', 'description': f'Threat intelligence detected: {threat} for port {rule["port"]}'})
    return vulnerabilities

# Route for main firewall page
@app.route('/')
def firewall_page():
    vulnerabilities = check_vulnerabilities()
    return render_template('firewall.html', firewall_rules=firewall_rules, vulnerabilities=vulnerabilities)

# Route to fetch open ports
@app.route('/get_open_ports')
def get_open_ports():
    ports = scan_ports()
    return jsonify({'open_ports': ports})

# Route to add a new port
@app.route('/add_port', methods=['POST'])
def add_port():
    new_port = int(request.form['port'])
    protocol = request.form['protocol']
    # Add logic to store new_port and protocol in configuration
    return 'Port added successfully'

# Route to add a new firewall rule
@app.route('/add_firewall_rule', methods=['POST'])
def add_firewall_rule():
    protocol = request.form['protocol']
    port = int(request.form['port'])
    action = request.form['action']
    rule_id = get_next_rule_id()
    new_rule = {'rule_id': rule_id, 'type': 'firewall', 'protocol': protocol, 'port': port, 'action': action}
    firewall_rules.append(new_rule)
    return 'Firewall rule added successfully'

# Route to add a new port forwarding rule
@app.route('/add_port_forwarding', methods=['POST'])
def add_port_forwarding():
    protocol = request.form['protocol']
    source_port = int(request.form['source_port'])
    source_ip = request.form['source_ip']
    dest_ip = request.form['dest_ip']
    dest_port = int(request.form['dest_port'])
    rule_id = get_next_rule_id()
    new_rule = {'rule_id': rule_id, 'type': 'port_forward', 'protocol': protocol, 'source_port': source_port, 'source_ip': source_ip, 'dest_ip': dest_ip, 'dest_port': dest_port}
    firewall_rules.append(new_rule)
    return 'Port forwarding rule added successfully'

if __name__ == '__main__':
    app.run(debug=True)

