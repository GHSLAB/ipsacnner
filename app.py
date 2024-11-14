import subprocess
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import ipaddress


## Create Placeholder class
class PlaceholderEntry(tk.Entry):

    def __init__(self, master=None, placeholder="Enter text", color="gray"):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        self._add_placeholder()  # Add placeholder during initialization

    def _clear_placeholder(self, event=None):
        if self["fg"] == self.placeholder_color:
            self.delete(0, tk.END)
            self["fg"] = self.default_fg_color

    def _add_placeholder(self, event=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self["fg"] = self.placeholder_color


def ping_ip(ip):
    """Use subprocess module to run ping command and check if the specified IP address is reachable"""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "500", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,  # Raise an exception if the command fails
        )
        if "TTL=" in result.stdout.decode("gbk"):
            return ip
    except subprocess.CalledProcessError:
        return None


def get_scan_ip_list(input_str: str) -> list:
    """Get the scan list"""
    input_text = input_str.replace("，", ",")
    return [f"{base_ip}.{i}" for base_ip in input_text.split(",") for i in range(1, 256)]


def get_occupied_ips(ip_list: list, max_workers=100, progress_bar=None) -> list:
    """Get the list of occupied IP addresses in the specified subnet using multithreading, return as list"""
    occupied_ips = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_ip = {executor.submit(ping_ip, ip): ip for ip in ip_list}
        for i, future in enumerate(as_completed(future_to_ip)):
            ip = future_to_ip[future]
            try:
                result = future.result()
                if result:
                    occupied_ips.append(result)
            except Exception as e:
                print(f"Error scanning {ip}: {e}")
            if progress_bar:
                progress_bar["value"] = i + 1
                progress_bar.update_idletasks()

    return occupied_ips


def get_available_ips(base_ip: str, occupied_ips: list) -> list:
    """Get the list of available IP addresses in the specified subnet"""
    occupied_set = set(occupied_ips)
    return [f"{base_ip}.{i}" for i in range(1, 256) if f"{base_ip}.{i}" not in occupied_set]


def sort_ip_list(ip_list: list) -> list:
    """Sort IP addresses by converting them to numeric form"""
    return sorted(ip_list, key=lambda ip: int(ipaddress.ip_address(ip)))


def export_to_excel():
    """Export contents of result_text and available_text to an Excel spreadsheet"""
    occupied_ips = result_text.get(1.0, tk.END).strip().split("\n")
    available_ips = available_text.get(1.0, tk.END).strip().split("\n")

    df_occupied = pd.DataFrame(occupied_ips, columns=["Occupied IPs"])
    df_available = pd.DataFrame(available_ips, columns=["Available IPs"])

    try:
        with pd.ExcelWriter("IP_Scan_Results.xlsx") as writer:
            df_occupied.to_excel(writer, sheet_name="Occupied IPs", index=False)
            df_available.to_excel(writer, sheet_name="Available IPs", index=False)
        messagebox.showinfo(
            "Export Successful", "Results have been exported to IP_Scan_Results.xlsx"
        )
    except Exception as e:
        messagebox.showerror("Export Failed", f"Error: {e}")


def scan_ips():
    """Scan IP addresses"""
    input_text = entry.get()

    if not input_text:
        messagebox.showerror("Error", "Please enter a subnet")
        return

    base_ip = get_scan_ip_list(input_text)
    progress_bar["maximum"] = 255
    progress_bar["value"] = 0

    threading.Thread(target=lambda: scan_thread(base_ip), daemon=True).start()


def scan_thread(base_ip):
    """Scanning thread"""
    occupied_ips = sort_ip_list(get_occupied_ips(base_ip, progress_bar=progress_bar))
    available_ips = sort_ip_list(get_available_ips(base_ip[0].rsplit(".", 1)[0], occupied_ips))

    result_text.delete(1.0, tk.END)
    available_text.delete(1.0, tk.END)

    result_text.insert(tk.END, "\n".join(occupied_ips) + "\n")
    available_text.insert(tk.END, "\n".join(available_ips) + "\n")

    progress_bar["value"] = 255  # Complete the progress bar


# Create the main window
root = tk.Tk()
root.title("IP Scanner")
root.resizable(False, False)

# Layout
input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

label = ttk.Label(input_frame, text="Input Subnet:")
label.grid(row=0, column=0, padx=10)

# Input box
entry = PlaceholderEntry(input_frame, placeholder="e.g. 192.168.100")
entry.grid(row=0, column=1, padx=10)

scan_button = ttk.Button(input_frame, text="Scan", width=10, command=scan_ips)
scan_button.grid(row=0, column=2, padx=10)

# Progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

# Output box
label_frame = ttk.Frame(root)
label_frame.pack(pady=5)

result_label = ttk.Label(label_frame, text="Occupied IP")
result_label.grid(row=0, column=0, padx=10)

available_label = ttk.Label(label_frame, text="Available IP")
available_label.grid(row=0, column=1, padx=10)

paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill="both", expand=True, pady=5, padx=5)

result_text = tk.Text(paned_window, width=25, height=30)
paned_window.add(result_text)

available_text = tk.Text(paned_window, width=25, height=30)
paned_window.add(available_text)

export_button = ttk.Button(root, text="Export Table", command=export_to_excel)
export_button.pack(side=tk.RIGHT, pady=5, padx=5)

# Run the main loop
root.mainloop()
