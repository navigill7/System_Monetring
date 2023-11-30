import tkinter as tk
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import psutil
from email.message import EmailMessage
import ssl
import smtplib
import threading

matplotlib.use('Agg') 

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

# Create the main application window
class SystemMonitorApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "System Monitor")

        # Set up the figure and axes for CPU, RAM, Network, and Disk
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(12, 10))

        # Lists to store data for plotting
        self.time = []
        self.cpu_percentages = []
        self.ram_percentages = []
        self.network_bytes = []
        self.disk_percentages = []

        # Animation
        self.ani = FuncAnimation(self.fig, self.update)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # Function to update data for animation
    def update(self, frame):
        # Get current CPU, RAM, network, and disk usage
        cpu_percentage = psutil.cpu_percent(interval=2)
        ram_percentage = psutil.virtual_memory().percent
        network_bytes_sent = psutil.net_io_counters().bytes_sent
        network_bytes_recv = psutil.net_io_counters().bytes_recv
        disk_info = psutil.disk_usage('/')
        disk_percentage = disk_info.percent

        # Calculate total network usage in bytes per second
        network_usage = network_bytes_sent + network_bytes_recv

        # Check danger thresholds and send email alert if exceeded
        self.check_danger('CPU', cpu_percentage)
        self.check_danger('RAM', ram_percentage)
        self.check_danger('Network', network_usage)
        self.check_danger('Disk', disk_percentage)

        # Get high CPU usage processes
        high_cpu_processes = self.get_high_cpu_processes()
        # Suggest actions for high CPU usage processes
        process_actions = self.suggest_process_actions(high_cpu_processes)

        # Getting The Running Applications
        running_apps = self.get_running_apps()
        # Write the list of running applications to a text file
        self.write_running_apps_to_file(running_apps)

        # Consolidate information into a single email
        email_content = (
            "Alert!!\n\n"
            "Running Applications:\n\n"
            "{}\n\n".format('\n'.join(running_apps))
        )

        for parameter, value in [('CPU', cpu_percentage), ('RAM', ram_percentage), ('Network', network_usage),
                                 ('Disk', disk_percentage)]:
            if not alert_sent[parameter] and value > danger_threshold[parameter]:
                email_content += f"{parameter} Exceeded: {value}\nSuggested Action: {self.suggest_action(parameter)}\n\n"
                alert_sent[parameter] = True

        # Send email with attached running apps text file asynchronously
        threading.Thread(target=self.send_email_alert, args=(email_content, 'running_apps.txt')).start()

        # Append data to lists
        self.time.append(frame)
        self.cpu_percentages.append(cpu_percentage)
        self.ram_percentages.append(ram_percentage)
        self.network_bytes.append(network_usage)
        self.disk_percentages.append(disk_percentage)

        # Limit data to the last 50 entries for better visualization
        if len(self.time) > 50:
            self.time.pop(0)
            self.cpu_percentages.pop(0)
            self.ram_percentages.pop(0)
            self.network_bytes.pop(0)
            self.disk_percentages.pop(0)

        # Plot CPU usage
        self.ax1.clear()
        self.ax1.plot(self.time, self.cpu_percentages, label='CPU Usage', color='blue')
        self.ax1.set_title('CPU Usage')
        self.ax1.set_ylim(0, 100)
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('Percentage')
        self.ax1.legend()

        # Display current CPU percentage
        self.ax1.text(0.02, 0.92, f'Current CPU: {cpu_percentage:.2f}%', transform=self.ax1.transAxes, color='blue')

        # Plot RAM usage
        self.ax2.clear()
        self.ax2.plot(self.time, self.ram_percentages, label='RAM Usage', color='green')
        self.ax2.set_title('RAM Usage')
        self.ax2.set_ylim(0, 100)
        self.ax2.set_xlabel('Time')
        self.ax2.set_ylabel('Percentage')
        self.ax2.legend()

        # Display current RAM percentage
        self.ax2.text(0.02, 0.92, f'Current RAM: {ram_percentage:.2f}%', transform=self.ax2.transAxes, color='green')

        # Plot Network usage in bytes per second
        self.ax3.clear()
        self.ax3.plot(self.time, self.network_bytes, label='Network Usage', color='orange')
        self.ax3.set_title('Network Usage')
        self.ax3.set_xlabel('Time')
        self.ax3.set_ylabel('Bytes per Second')
        self.ax3.legend()

        # Display current Network usage
        self.ax3.text(0.02, 0.92, f'Current Network: {network_usage} bytes/s', transform=self.ax3.transAxes,
                      color='orange')

        # Plot Disk usage
        self.ax4.clear()
        self.ax4.plot(self.time, self.disk_percentages, label='Disk Usage', color='red')
        self.ax4.set_title('Disk Usage')
        self.ax4.set_ylim(0, 100)
        self.ax4.set_xlabel('Time')
        self.ax4.set_ylabel('Percentage')
        self.ax4.legend()

        # Display current Disk percentage
        self.ax4.text(0.02, 0.92, f'Current Disk: {disk_percentage:.2f}%', transform=self.ax4.transAxes, color='red')

                # Display process actions
        print("\n".join(process_actions))

        # Redraw the canvas
        self.canvas.draw()

    def write_running_apps_to_file(self, running_apps):
        with open('running_apps.txt', 'w') as file:
            file.write('\n'.join(running_apps))

    def get_running_apps(self):
        apps = []
        for process in psutil.process_iter(attrs=['pid', 'name']):
            try:
                apps.append(f"Running App: {process.info['name']} (PID: {process.info['pid']})")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return apps

    # Function to check danger thresholds and send email alert if exceeded
    def check_danger(self, parameter, value):
        if not alert_sent[parameter] and value > danger_threshold[parameter]:
            self.send_email_alert(parameter, value)
            alert_sent[parameter] = True  # Set the flag to True once an email is sent

    # Function to send email alert
    def send_email_alert(self, parameter, value, attachment_filename=None):
        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = f"{subject} - {parameter} Exceeded"
        em.set_content(f"Alert!!\nCurrent {parameter} usage: {value}\n\nSuggested Action: {self.suggest_action(parameter)}")

        if attachment_filename:
            # Attach the running apps text file
            with open(attachment_filename, 'rb') as file:
                em.add_attachment(file.read(), maintype='application', subtype='octet-stream', filename=attachment_filename)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_pass)
            smtp.sendmail(email_sender, email_receiver, em.as_string())

    # Function to suggest action based on the parameter that exceeded the threshold
    def suggest_action(self, parameter):
        if parameter == 'CPU':
            return "Consider closing unused applications or optimizing running processes."
        elif parameter == 'RAM':
            return "Close unnecessary programs or increase RAM capacity if possible."
        elif parameter == 'Network':
            return "Check for bandwidth-intensive applications or consider upgrading your network connection."
        elif parameter == 'Disk':
            return "Free up disk space or consider upgrading your storage capacity."

    # Function to get a list of processes sorted by CPU usage
    def get_high_cpu_processes(self):
        processes = []
        for process in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                if process.info['cpu_percent'] > 10:
                    processes.append(process.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)

    # Function to suggest actions for high CPU usage processes
    def suggest_process_actions(self, high_cpu_processes):
        actions = []
        for process in high_cpu_processes:
            actions.append(
                f"High CPU Usage: {process['name']} (PID: {process['pid']}) - CPU Percent: {process['cpu_percent']:.2f}%")
        return actions


# Create the application instance
app = SystemMonitorApp()
# Run the Tkinter main loop
app.mainloop()
