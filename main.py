import os
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from threading import Thread, Event
import time
import subprocess
class DownloadManager:
    def __init__(self):
        self.load_config()  # Load SSH server details from the config file

        self.app = tk.Tk()
        self.app.title("Download Manager")
        self.app.configure(bg="#2e2e2e")  # Set dark background color

        self.frame = tk.Frame(self.app, padx=20, pady=20, bg="#2e2e2e")  # Set dark background color
        self.frame.pack()

        self.label_url = tk.Label(self.frame, text="URL:", bg="#2e2e2e", fg="white")  # Set dark background color and white text
        self.label_url.grid(row=0, column=0)
        self.entry_url = tk.Entry(self.frame)
        self.entry_url.grid(row=0, column=1)

        self.button_download = tk.Button(self.frame, text="Download", command=self.download_file, bg="#4CAF50", fg="white")  # Set button color
        self.button_download.grid(row=4, column=1, sticky="e")

        self.button_stop = tk.Button(self.frame, text="Stop", command=self.stop_download, bg="#FF0000", fg="white")  # Set button color
        self.button_stop.grid(row=4, column=2, sticky="w")
        self.button_stop["state"] = "disabled"  # Initially disable the "Stop" button

        self.label_percentage = tk.Label(self.frame, text="", bg="#2e2e2e", fg="white")  # Set dark background color and white text
        self.label_percentage.grid(row=5, column=1, sticky="e")

        self.label_download_size = tk.Label(self.frame, text="", bg="#2e2e2e", fg="white")
        self.label_download_size.grid(row=7, column=1, sticky="e")

        self.label_bandwidth = tk.Label(self.frame, text="", bg="#2e2e2e", fg="white")
        self.label_bandwidth.grid(row=8, column=1, sticky="e")

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.frame, variable=self.progress_var, orient=tk.HORIZONTAL, length=200, mode='determinate', style="TProgressbar")  # Set style for the progress bar
        self.progress_bar.grid(row=6, column=1, sticky="e")

        self.download_thread = None  # To store the download thread
        self.stop_download_flag = Event()  # Event flag to signal stopping the download

    def load_config(self):
        config = configparser.ConfigParser()
        config.read("config.ini")

        # Read SSH server details from the config file
        self.ssh_ip = config.get("SSH", "ip", fallback="")
        self.ssh_username = config.get("SSH", "username", fallback="")
        self.ssh_password = config.get("SSH", "password", fallback="")

    def download_file(self):
        try:
            url = self.entry_url.get()

            # Set default download location to desktop
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            local_path = filedialog.askdirectory(initialdir=desktop_path)

            # Extract the filename from the URL
            filename = os.path.basename(url)
            local_path = os.path.join(local_path, filename)

            # Download file using requests
            self.download_thread = Thread(target=self.http_download, args=(url, local_path))
            self.download_thread.start()

            # Disable the "Download" button and enable the "Stop" button
            self.button_download["state"] = "disabled"
            self.button_stop["state"] = "active"
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def http_download(self, url, local_path):
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))

            start_time = time.time()
            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if self.stop_download_flag.is_set():
                    break

                with open(local_path, 'ab') as file:
                    file.write(chunk)

                downloaded_size += len(chunk)

                # Update progress bar and percentage label
                percentage = (downloaded_size / total_size) * 100
                self.progress_var.set(percentage)
                self.label_percentage["text"] = f"{percentage:.2f}%"

                # Update the downloaded size in MB
                downloaded_size_mb = downloaded_size / (1024 * 1024)
                downloaded_size_mb_str = f"{downloaded_size_mb:.2f} MB"
                self.label_download_size["text"] = f"Downloaded: {downloaded_size_mb_str}"

                # Update download bandwidth if elapsed_time is not zero
                elapsed_time = time.time() - start_time
                if elapsed_time > 0:
                    bandwidth = downloaded_size / (1024 * elapsed_time)
                    bandwidth_str = f"{bandwidth:.2f} KB/s"
                    self.label_bandwidth["text"] = f"Bandwidth: {bandwidth_str}"

                self.app.update_idletasks()  # Update the GUI

            messagebox.showinfo("Success", "Download has completed.")
        except requests.exceptions.RequestException as e:
            print(f"HTTP Download Error: {e}")
            messagebox.showerror("Error", f"Failed to download file: {e}")
        finally:
            # Enable the "Download" button and disable the "Stop" button
            self.button_download["state"] = "active"
            self.button_stop["state"] = "disabled"

    def stop_download(self):
        if self.download_thread and self.download_thread.is_alive():
            # Set the stop flag to signal the download thread to stop
            self.stop_download_flag.set()
            # Wait for the download thread to finish
            self.download_thread.join()
            # Reset the stop flag for future downloads
            self.stop_download_flag.clear()

            messagebox.showinfo("Info", "Download has been stopped.")
        else:
            messagebox.showinfo("Info", "No active download to stop.")

    def run(self):
        self.app.mainloop()
    
def check_for_update(repo_url, local_path):
    
    if os.path.exists(local_path):
        
        subprocess.run(["git", "-C", local_path, "fetch", "origin", "main"], check=True)
        
        
        latest_commit_sha = subprocess.check_output(
            ["git", "-C", local_path, "rev-parse", "origin/main"],
            universal_newlines=True
        ).strip()
        
        
        try:
            current_commit_sha = subprocess.check_output(
                ["git", "-C", local_path, "rev-parse", "HEAD"],
                universal_newlines=True
            ).strip()
        except subprocess.CalledProcessError:
            current_commit_sha = None
        
        
        if current_commit_sha != latest_commit_sha:
            print("Update available!")
            update_choice = input("Do you want to update? (yes/no): ").lower()
            
            if update_choice == "yes":
                
                subprocess.run(["git", "-C", local_path, "pull", "origin", "main"], check=True)
                print("Update complete.")
            else:
                print("No update performed.")
        else:
            print("You already have the latest version.")
    else:
        # If the local repository doesn't exist, clone it in the script's directory
        subprocess.run(["git", "clone", repo_url, local_path], check=True)
        print("Repository cloned.")
if __name__ == "__main__":
    script_directory = os.path.dirname(os.path.abspath(__file__))

    
    github_repo_url = "https://github.com/Itzhep/InternetDownload-manager"
    local_repository_path = os.path.join(script_directory, "Updated-Script")

    check_for_update(github_repo_url, local_repository_path)
    manager = DownloadManager()
    manager.run()
