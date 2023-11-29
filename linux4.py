import psutil
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from email.message import EmailMessage
import ssl
import smtplib

# Email configuration
email_sender = "nnavigill784@gmail.com"
email_pass = "acqk xqae vksj glqs"
email_receiver = 'e22cseu1384@bennett.edu.in'
subject = "System Monitoring Alert"

# Danger threshold for each parameter
danger_threshold = {
    'CPU': 80,
    'RAM': 80,
    'Network': 1000000,  # Danger threshold for network usage in bytes per second
    'Disk': 80
}

# Flags to track whether an alert email has been sent for each parameter
alert_sent = {
    'CPU': False,
    'RAM': False,
    'Network': False,
    'Disk': False
}

# Initialize figures and axes for CPU, RAM, Network, and Disk
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# Lists to store data for plotting
time = []
cpu_percentages = []
ram_percentages = []
network_bytes = []
disk_percentages = []

# Function to update data for animation
def update(frame):
    # Get current CPU, RAM, network, and disk usage
    cpu_percentage = psutil.cpu_percent(interval=1)
    ram_percentage = psutil.virtual_memory().percent
    network_bytes_sent = psutil.net_io_counters().bytes_sent
    network_bytes_recv = psutil.net_io_counters().bytes_recv
    disk_info = psutil.disk_usage('/')
    disk_percentage = disk_info.percent

    # Calculate total network usage in bytes per second
    network_usage = network_bytes_sent + network_bytes_recv

    # Check danger thresholds and send email alert if exceeded
    check_danger('CPU', cpu_percentage)
    check_danger('RAM', ram_percentage)
    check_danger('Network', network_usage)
    check_danger('Disk', disk_percentage)

    # Get high CPU usage processes
    high_cpu_processes = get_high_cpu_processes()
    # Suggest actions for high CPU usage processes
    process_actions = suggest_process_actions(high_cpu_processes)

    # Append data to lists
    time.append(frame)
    cpu_percentages.append(cpu_percentage)
    ram_percentages.append(ram_percentage)
    network_bytes.append(network_usage)
    disk_percentages.append(disk_percentage)

    # Limit data to the last 50 entries for better visualization
    if len(time) > 50:
        time.pop(0)
        cpu_percentages.pop(0)
        ram_percentages.pop(0)
        network_bytes.pop(0)
        disk_percentages.pop(0)

    # Plot CPU usage
    ax1.clear()
    ax1.plot(time, cpu_percentages, label='CPU Usage', color='blue')
    ax1.set_title('CPU Usage')
    ax1.set_ylim(0, 100)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Percentage')
    ax1.legend()

    # Display current CPU percentage
    ax1.text(0.02, 0.92, f'Current CPU: {cpu_percentage:.2f}%', transform=ax1.transAxes, color='blue')

    # Plot RAM usage
    ax2.clear()
    ax2.plot(time, ram_percentages, label='RAM Usage', color='green')
    ax2.set_title('RAM Usage')
    ax2.set_ylim(0, 100)
    ax2.set_xlabel('Time')
    ax2.set_ylabel('Percentage')
    ax2.legend()

    # Display current RAM percentage
    ax2.text(0.02, 0.92, f'Current RAM: {ram_percentage:.2f}%', transform=ax2.transAxes, color='green')

    # Plot Network usage in bytes per second
    ax3.clear()
    ax3.plot(time, network_bytes, label='Network Usage', color='orange')
    ax3.set_title('Network Usage')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('Bytes per Second')
    ax3.legend()

    # Display current Network usage
    ax3.text(0.02, 0.92, f'Current Network: {network_usage} bytes/s', transform=ax3.transAxes, color='orange')

    # Plot Disk usage
    ax4.clear()
    ax4.plot(time, disk_percentages, label='Disk Usage', color='red')
    ax4.set_title('Disk Usage')
    ax4.set_ylim(0, 100)
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Percentage')
    ax4.legend()

    # Display current Disk percentage
    ax4.text(0.02, 0.92, f'Current Disk: {disk_percentage:.2f}%', transform=ax4.transAxes, color='red')

    # Display process actions
    print("\n".join(process_actions))

# Function to check danger thresholds and send email alert if exceeded
def check_danger(parameter, value):
    if not alert_sent[parameter] and value > danger_threshold[parameter]:
        send_email_alert(parameter, value)
        alert_sent[parameter] = True  # Set the flag to True once an email is sent

# Function to send email alert
def send_email_alert(parameter, value):
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = f"{subject} - {parameter} Exceeded"
    em.set_content(f"Alert!!\nCurrent {parameter} usage: {value}\n\nSuggested Action: {suggest_action(parameter)}")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_pass)
        smtp.sendmail(email_sender, email_receiver, em.as_string())

# Function to suggest action based on the parameter that exceeded the threshold
def suggest_action(parameter):
    if parameter == 'CPU':
        return "Consider closing unused applications or optimizing running processes."
    elif parameter == 'RAM':
        return "Close unnecessary programs or increase RAM capacity if possible."
    elif parameter == 'Network':
        return "Check for bandwidth-intensive applications or consider upgrading your network connection."
    elif parameter == 'Disk':
        return "Free up disk space or consider upgrading your storage capacity."

# Function to get a list of processes sorted by CPU usage
def get_high_cpu_processes():
    processes = []
    for process in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            if process.info['cpu_percent'] > 10:  # Adjust the threshold as needed
                processes.append(process.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)

# Function to suggest actions based on high CPU usage processes
def suggest_process_actions(processes):
    suggestions = []
    for process in processes:
        suggestions.append(f"Process '{process['name']}' with PID {process['pid']} is using {process['cpu_percent']}% CPU. Consider investigating or terminating this process.")
    return suggestions
ani = FuncAnimation(fig, update, blit=False)

# Show the animated plot
plt.tight_layout()
plt.show()