import subprocess
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import threading
import ipaddress
import os

current_path = os.path.abspath(os.getcwd())


## 新建Placehoder类
class PlaceholderEntry(tk.Entry):
    """灰色占位符类"""

    def __init__(self, master=None, placeholder="请输入文本", color="gray"):
        super().__init__(master)

        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self["fg"]

        self.bind("<FocusIn>", self._clear_placeholder)
        self.bind("<FocusOut>", self._add_placeholder)

        self._add_placeholder()  # 初始化时添加占位符

    def _clear_placeholder(self, event=None):
        if self["fg"] == self.placeholder_color:
            self.delete(0, tk.END)
            self["fg"] = self.default_fg_color

    def _add_placeholder(self, event=None):
        if not self.get():
            self.insert(0, self.placeholder)
            self["fg"] = self.placeholder_color


def ping_ip(ip):
    """使用subprocess模块运行ping命令,检查指定IP地址是否可达"""
    try:
        result = subprocess.run(
            ["ping", "-n", "1", "-w", "500", ip],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,  # 如果命令失败，抛出异常
        )
        if "TTL=" in result.stdout.decode("gbk"):
            return ip
    except subprocess.CalledProcessError:
        return None


def get_scan_ip_list(input_str: str) -> list:
    """获取扫描列表"""
    input_text = input_str.replace("，", ",")
    return [f"{base_ip}.{i}" for base_ip in input_text.split(",") for i in range(1, 256)]


def get_occupied_ips(ip_list: list, max_workers=100, progress_bar=None) -> list:
    """多线程获取指定网段中已被占用的IP地址列表, 返回为list"""
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
    """获取指定网段中可用的IP地址列表"""
    occupied_set = set(occupied_ips)
    return [f"{base_ip}.{i}" for i in range(1, 256) if f"{base_ip}.{i}" not in occupied_set]


def sort_ip_list(ip_list: list) -> list:
    """将IP地址转换为数值形式进行排序"""
    return sorted(ip_list, key=lambda ip: int(ipaddress.ip_address(ip)))


def export_to_excel():
    """将result_text和available_text中的内容导出至Excel表格"""
    occupied_ips = result_text.get(1.0, tk.END).strip().split("\n")
    available_ips = available_text.get(1.0, tk.END).strip().split("\n")

    df_occupied = pd.DataFrame(occupied_ips, columns=["Occupied IPs"])
    df_available = pd.DataFrame(available_ips, columns=["Available IPs"])

    try:
        with pd.ExcelWriter("IP_Scan_Results.xlsx") as writer:
            df_occupied.to_excel(writer, sheet_name="Occupied IPs", index=False)
            df_available.to_excel(writer, sheet_name="Available IPs", index=False)
        messagebox.showinfo("导出成功", "结果已导出至IP_Scan_Results.xlsx")
    except Exception as e:
        messagebox.showerror("导出失败", f"错误: {e}")


def scan_ips():
    """扫描IP地址"""
    input_text = entry.get()

    if not input_text:
        messagebox.showerror("错误", "请输入网段")
        return

    base_ip = get_scan_ip_list(input_text)
    progress_bar["maximum"] = 255
    progress_bar["value"] = 0

    threading.Thread(target=lambda: scan_thread(base_ip), daemon=True).start()


def scan_thread(base_ip):
    """扫描线程"""
    occupied_ips = sort_ip_list(get_occupied_ips(base_ip, progress_bar=progress_bar))
    available_ips = sort_ip_list(get_available_ips(base_ip[0].rsplit(".", 1)[0], occupied_ips))

    result_text.delete(1.0, tk.END)
    available_text.delete(1.0, tk.END)

    result_text.insert(tk.END, "\n".join(occupied_ips) + "\n")
    available_text.insert(tk.END, "\n".join(available_ips) + "\n")

    progress_bar["value"] = 255  # 完成进度条


# 创建主窗口
root = tk.Tk()
root.title("IP Scanner")
root.resizable(False, False)

# Layout
input_frame = ttk.Frame(root)
input_frame.pack(pady=10)

label = ttk.Label(input_frame, text="输入网段:")
label.grid(row=0, column=0, padx=10)

# 输入框
entry = PlaceholderEntry(input_frame, placeholder="e.g. 192.168.100")
entry.grid(row=0, column=1, padx=10)

scan_button = ttk.Button(input_frame, text="扫描", width=10, command=scan_ips)
scan_button.grid(row=0, column=2, padx=10)

# 进度条
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

# 输出框
label_frame = ttk.Frame(root)
label_frame.pack(pady=5)

result_label = ttk.Label(label_frame, text="已用IP")
result_label.grid(row=0, column=0, padx=10)

available_label = ttk.Label(label_frame, text="可用IP")
available_label.grid(row=0, column=1, padx=10)

paned_window = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
paned_window.pack(fill="both", expand=True, pady=5, padx=5)

result_text = tk.Text(paned_window, width=25, height=30)
paned_window.add(result_text)

available_text = tk.Text(paned_window, width=25, height=30)
paned_window.add(available_text)

export_button = ttk.Button(root, text="导出表格", command=export_to_excel)
export_button.pack(side=tk.RIGHT, pady=5, padx=5)

# 运行主循环
root.mainloop()
