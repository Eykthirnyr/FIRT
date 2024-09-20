import os
import sys
import time
import threading
import webbrowser
from tkinter import Tk, Label, StringVar, Button, Entry, OptionMenu, StringVar, filedialog, DISABLED, NORMAL, Toplevel
from datetime import timedelta, datetime
import subprocess

# Global variables
total_files = 0
remaining_files = 0
readable_files = 0
unreadable_files = 0
skipped_files = 0
error_files = []
is_running = False
scan_thread = None
start_time = None
paused_duration = timedelta()
timeout_duration = 10  # Default timeout
scan_path = "C:\\"  # Default drive
log_file_path = ""  # Will be set dynamically

# Function to reset the app by closing and reopening it
def reset_app():
    python = sys.executable
    script = os.path.abspath(__file__)
    subprocess.Popen([python, script])  # Start a new instance of the script
    root.destroy()  # Close the current instance

# Function to validate user input
def validate_inputs():
    global timeout_duration, scan_path

    # Validate timeout
    try:
        timeout_duration = int(timeout_entry.get())
        if timeout_duration > 10000:
            timeout_duration = 10
            timeout_entry.delete(0, 'end')
            timeout_entry.insert(0, "10")
    except ValueError:
        timeout_duration = 10
        timeout_entry.delete(0, 'end')
        timeout_entry.insert(0, "10")
    
    # Validate drive letter or folder input
    if scan_type_var.get() == "Drive":
        drive_letter = drive_path_var.get().strip()
        if len(drive_letter) > 2 or not drive_letter.isalpha():
            drive_letter = "C:"
            drive_path_var.set("C:")
        scan_path = f"{drive_letter}\\"
    elif scan_type_var.get() == "Local Folder or Network Folder":
        scan_path = selected_folder_path_var.get()

    # Check if path exists
    if not os.path.exists(scan_path):
        stop_scan()  # Stop the scan if the path is invalid
        display_error_message("Error: Path Not Found")
        return False
    
    return True

# Function to display an error message for 10 seconds
def display_error_message(message):
    error_message_label.config(text=message, fg="red")
    root.after(10000, lambda: error_message_label.config(text=""))

# Function to log errors to a file
def log_error(file_path, error_message):
    log_file = initialize_default_log_file()
    with open(log_file, 'a') as log_file:
        log_file.write(f"Error reading {file_path}: {error_message}\n")

# Function to log skipped files
def log_skipped(file_path):
    log_file = initialize_default_log_file()
    with open(log_file, 'a') as log_file:
        log_file.write(f"Skipped file {file_path}: Took longer than {timeout_duration} seconds to process.\n")

# Function to read a file with a timeout
def read_file_with_timeout(file_path):
    try:
        with open(file_path, 'rb') as f:
            f.read()  # Attempt to read the file
        return True
    except Exception as e:
        log_error(file_path, str(e))
        return False

# Function to attempt reading a file with timeout using threading
def process_file(file_path):
    success = False  # Declare success locally in this scope

    def target():
        nonlocal success  # Bind success within the thread target
        success = read_file_with_timeout(file_path)

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout_duration)

    if thread.is_alive():
        global skipped_files
        skipped_files += 1
        log_skipped(file_path)
        return False
    return success

# Function to count the total number of files recursively
def count_total_files(scan_path):
    file_count = 0
    for root_dir, dirs, files in os.walk(scan_path):
        file_count += len(files)
    return file_count

# Function to scan and test file readability
def test_file_readability(scan_path):
    global total_files, readable_files, unreadable_files, skipped_files, remaining_files, is_running

    status_var.set("Status: Loading")  # Set loading status
    remaining_files = count_total_files(scan_path)
    status_var.set("Status: Running")  # Change to running after counting is done
    current_scan_path_var.set(f"Scanning: {scan_path}")  # Update current path display

    for root_dir, dirs, files in os.walk(scan_path):
        if not is_running:
            break
        for file in files:
            if not is_running:
                break
            
            file_path = os.path.join(root_dir, file)
            total_files += 1
            remaining_files -= 1
            try:
                if process_file(file_path):
                    readable_files += 1
                else:
                    unreadable_files += 1
            except Exception as e:
                unreadable_files += 1
                log_error(file_path, str(e))
            
            # Update status and progress in the log and GUI
            if total_files >= 2:
                status_var.set("Status: Running")
            if remaining_files == 0:
                status_var.set("Status: Finished")

            processed_files_var.set(f"Processed Files: {total_files}")
            remaining_files_var.set(f"Remaining Files: {remaining_files}")
            failed_files_var.set(f"Failed Reads: {unreadable_files}")
            skipped_files_var.set(f"Skipped Files: {skipped_files}")
            root.update()

    finalize_scan()

# Function to finalize the scan (write the summary and log)
def finalize_scan():
    global is_running
    if is_running:
        is_running = False
        write_log_summary()
        start_button.config(state=DISABLED)
        stop_button.config(text="Reset", command=reset_app, state=NORMAL)  # Change "Stop" to "Reset" and link to reset_app
        log_folder_button.config(state=DISABLED)  # Disable select folder after scan
        status_var.set("Status: Finished")
        open_log_button.config(state=NORMAL)  # Enable Open Log button
        open_log_folder_button.config(state=NORMAL)  # Enable Open Log Folder button

# Function to write summary to log
def write_log_summary():
    log_file = initialize_default_log_file()
    total_time = time.time() - start_time if start_time else 0
    with open(log_file, 'a') as log_file:
        log_file.write(f"\nSummary:\n")
        log_file.write(f"Total files scanned: {total_files}\n")
        log_file.write(f"Readable files: {readable_files}\n")
        log_file.write(f"Unreadable files: {unreadable_files}\n")
        log_file.write(f"Skipped files: {skipped_files}\n")
        log_file.write(f"Time taken: {str(timedelta(seconds=int(total_time)))}\n")
        log_file.write(f"Path scanned: {scan_path}\n")  # Log scanned path at the end

# Timer functions
def update_timer():
    if is_running:
        elapsed_time = timedelta(seconds=int(time.time() - start_time))
        elapsed_time_var.set(f"Elapsed Time: {str(elapsed_time)}")
        root.after(1000, update_timer)

# Start and Stop functions
def start_scan():
    global is_running, scan_thread, start_time
    if not is_running and validate_inputs():  # Validate inputs before starting
        is_running = True
        start_time = time.time()
        status_var.set("Status: Loading")  # Initial status before scan starts
        scan_thread = threading.Thread(target=test_file_readability, args=(scan_path,))
        scan_thread.start()
        update_timer()
        log_file = initialize_default_log_file()  # Display log file path
        start_button.config(state=DISABLED)  # Disable start button
        stop_button.config(state=NORMAL)  # Enable stop button
        log_folder_button.config(state=DISABLED)  # Disable "Select Log Folder" button during scan

def stop_scan():
    if is_running:
        finalize_scan()  # Stop and finalize the scan

# Function to handle focus in event for drive path
def drive_path_focus_in(event):
    if drive_path_entry.get() == "Enter drive letter (e.g., C:)":
        drive_path_entry.delete(0, "end")
        drive_path_entry.config(fg='black')

# Function to handle focus out event for drive path
def drive_path_focus_out(event):
    if drive_path_entry.get() == "":
        drive_path_entry.insert(0, "Enter drive letter (e.g., C:)")
        drive_path_entry.config(fg='grey')

# Function to initialize the default log file with the current date and time
def initialize_default_log_file():
    global log_file_path
    if not log_file_path:
        log_file_path = os.path.join(os.getcwd(), f"read_errors_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        log_file_path_var.set(f"Log file path: {log_file_path}")
    return log_file_path

# Function to open the log file
def open_log_file():
    if log_file_path:
        subprocess.run(['notepad.exe', log_file_path])

# Function to open the folder containing the log file
def open_log_folder():
    if log_file_path:
        log_folder = os.path.dirname(log_file_path)
        subprocess.run(['explorer', log_folder])

# Function to select a folder for the scan
def select_folder():
    global scan_path
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        scan_path = folder_selected
        selected_folder_path_var.set(folder_selected)
    else:
        selected_folder_path_var.set("Awaiting user folder selection")

# Function to select a folder for the log file
def choose_log_folder():
    global log_file_path
    log_folder = filedialog.askdirectory()
    if log_folder:
        log_file_path = os.path.join(log_folder, f"read_errors_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        log_file_path_var.set(f"Log file path: {log_file_path}")
        open_log_folder_button.config(state=NORMAL)  # Enable Open Log Folder button when log path is set

# Function to choose scan type
def choose_scan_type(selection):
    if selection == "Drive":
        drive_path_entry.config(state=NORMAL)
        select_folder_button.config(state=DISABLED)
    elif selection == "Local Folder or Network Folder":
        drive_path_entry.config(state=DISABLED)
        select_folder_button.config(state=NORMAL)

# Function to open the About popup with updated content and larger size
def open_about():
    about_window = Toplevel(root)
    about_window.title("About")
    about_window.geometry("600x650")  # Set window size to 600x600
    about_window.resizable(False, False)

    # Title and author information
    title_text = (
        "File Integrity & Readability Tester (FIRT)\n"
        "Made by Clément GHANEME\n"
        "Created: 2024\n\n"
    )

# Function to open the About popup with updated content, larger size, and disclaimer
def open_about():
    about_window = Toplevel(root)
    about_window.title("About")
    about_window.geometry("600x750")  # Set window size to 600x750
    about_window.resizable(False, False)

    # Title and author information
    title_text = (
        "File Integrity & Readability Tester (FIRT)\n"
        "Made by Clément GHANEME\n"
        "Created: 2024\n\n"
    )

    # Detailed description text
    about_text = (
        "The File Integrity & Readability Tester (FIRT) is a Python-based application designed for IT professionals "
        "and system administrators to assess file integrity across storage devices. It systematically scans a specified "
        "drive or directory, using multi-threading to maintain a responsive user interface while testing each file's readability. "
        "For each file, the application spawns a thread to execute a read operation within a user-defined timeout period. The read process "
        "involves attempting to open the file in binary mode and read its contents. If the file can be successfully read within the allotted time, "
        "it is marked as readable. If the operation times out or encounters an error, the file is logged as unreadable or skipped, and the exact "
        "error (e.g., permission denied, corrupted sectors) is documented in the log file. This design ensures the application can handle a large number of files, "
        "including those on potentially damaged or corrupted storage media, without freezing or becoming unresponsive.\n\n"
        
        "The application employs Tkinter for its graphical user interface, providing real-time updates on scan progress, including total files processed, "
        "remaining files, read failures, and skipped files. The UI supports different scan modes (full drive or specific directory) and allows configuration "
        "of scan parameters like the timeout duration. Results are logged in real-time to a text file, including detailed error messages and a summary of the scan's outcome. "
        "This log file's path is configurable and defaults to the script's directory if not specified. Upon completion or user interruption, the app finalizes the scan, "
        "writes a summary to the log, and can reset itself by restarting the entire process through the subprocess module.\n\n"
        
        "This software was developed to address a common issue in IT environments where standard tools fail to identify specific corrupted or unreadable files. "
        "Often, backup processes encounter errors due to corrupted sectors that go unnoticed by tools like SMART checks. After a partial backup or data recovery, "
        "it can be challenging to pinpoint which files were lost or corrupted. FIRT was created to fill this gap, offering a detailed analysis of file integrity to "
        "ensure no critical data is overlooked during backups or transfers.\n\n"
    )

    # Disclaimer text
    disclaimer_text = (
        "Disclaimer: This software is provided 'as is' without any guarantees or warranty. While it is designed to aid in assessing file integrity and readability, "
        "I cannot be held responsible for any loss, damage, or data corruption that may occur through its use. Users are advised to exercise caution and ensure they have proper backups before using this tool on critical systems."
    )

    # Title and creation info label
    title_label = Label(about_window, text=title_text, justify="center", font=('Helvetica', 12, 'bold'))
    title_label.pack(pady=(10, 0), padx=10)

    # Detailed description label
    about_label = Label(about_window, text=about_text, justify="left", wraplength=580, font=('Helvetica', 10))
    about_label.pack(pady=10, padx=10)

    # Disclaimer label
    disclaimer_label = Label(about_window, text=disclaimer_text, justify="left", wraplength=580, font=('Helvetica', 9, 'italic'), fg="red")
    disclaimer_label.pack(pady=(5, 10), padx=10)

    close_button = Button(about_window, text="Close", command=about_window.destroy)
    close_button.pack(pady=10)


# Create a Tkinter window for real-time progress display
root = Tk()
root.title("FIRT")  # Updated title
root.geometry("500x1000")  # Fixed window size
root.resizable(False, False)  # Non-resizable

# Tkinter string variables for dynamic updates
progress_var = StringVar()
status_var = StringVar()
elapsed_time_var = StringVar()
remaining_files_var = StringVar()
processed_files_var = StringVar()
failed_files_var = StringVar()
skipped_files_var = StringVar()
network_path_var = StringVar()
drive_path_var = StringVar()
selected_folder_path_var = StringVar()
log_file_path_var = StringVar()
current_scan_path_var = StringVar()

status_var.set("Status: Waiting for user input")
elapsed_time_var.set("Elapsed Time: 00:00:00")
remaining_files_var.set("Remaining Files: --")
processed_files_var.set("Processed Files: 0")
failed_files_var.set("Failed Reads: 0")
skipped_files_var.set("Skipped Files: 0")
current_scan_path_var.set("")  # Placeholder for current path display
selected_folder_path_var.set("Awaiting user folder selection")  # Placeholder for folder selection
log_file_path_var.set("Log file path: Not set yet")

# Title
title_label = Label(root, text="File Integrity & Readability Tester", font=('Helvetica', 20))
title_label.pack(pady=10)

# Short description of the main goal
description_label = Label(root, text="Quickly test file readability and integrity on local or network drives.", font=('Helvetica', 12))
description_label.pack(pady=5)

# Input for timeout and drive/folder selection
timeout_label = Label(root, text="Set Timeout (seconds):", font=('Helvetica', 14))
timeout_label.pack(pady=5)
timeout_entry = Entry(root)
timeout_entry.insert(0, "10")  # Default value for timeout
timeout_entry.pack(pady=5)

# Explanation for timeout
timeout_explanation = Label(root, text="Timeout defines the max time (in seconds) allowed to process each file before skipping it.", font=('Helvetica', 8))
timeout_explanation.pack(pady=5)

# Scan type selection
scan_type_label = Label(root, text="Choose Scan Type:", font=('Helvetica', 14))
scan_type_label.pack(pady=5)
scan_type_var = StringVar(root)
scan_type_var.set("Drive")  # Default scan type set to Drive
scan_type_menu = OptionMenu(root, scan_type_var, "Drive", "Local Folder or Network Folder", command=choose_scan_type)
scan_type_menu.pack(pady=5)

# Drive path entry
drive_label = Label(root, text="Enter Drive Letter or Select Folder:", font=('Helvetica', 14))  # Updated label
drive_label.pack(pady=5)
drive_path_entry = Entry(root, textvariable=drive_path_var)
drive_path_var.set("C:")  # Default to C drive
drive_path_entry.config(fg='grey')
drive_path_entry.bind("<FocusIn>", drive_path_focus_in)
drive_path_entry.bind("<FocusOut>", drive_path_focus_out)
drive_path_entry.pack(pady=5)

# Select folder button (for folder scan option)
select_folder_button = Button(root, text="Select Folder", command=select_folder, state=DISABLED)  # Disabled by default
select_folder_button.pack(pady=5)

# Non-editable label to display the selected folder path
selected_folder_path_label = Label(root, textvariable=selected_folder_path_var, font=('Helvetica', 10), relief="sunken")
selected_folder_path_label.pack(pady=5)

# Error message label (initially empty)
error_message_label = Label(root, text="", font=('Helvetica', 12), fg="red")
error_message_label.pack(pady=5)

# Status label (displaying "Waiting for user input", "Loading", "Running", "Finished")
status_label = Label(root, textvariable=status_var, font=('Helvetica', 16))
status_label.pack(pady=5)

# Label to display the current folder or drive being scanned
current_scan_path_label = Label(root, textvariable=current_scan_path_var, font=('Helvetica', 8))
current_scan_path_label.pack(pady=5)

# Tkinter labels to show live progress and timers
processed_files_label = Label(root, textvariable=processed_files_var, font=('Helvetica', 12))
processed_files_label.pack(pady=2)

remaining_files_label = Label(root, textvariable=remaining_files_var, font=('Helvetica', 12))
remaining_files_label.pack(pady=2)

elapsed_time_label = Label(root, textvariable=elapsed_time_var, font=('Helvetica', 12))
elapsed_time_label.pack(pady=2)

failed_files_label = Label(root, textvariable=failed_files_var, font=('Helvetica', 12))
failed_files_label.pack(pady=2)

skipped_files_label = Label(root, textvariable=skipped_files_var, font=('Helvetica', 12))
skipped_files_label.pack(pady=2)

# Log file path display (smaller text, wraps to new line if too long)
log_file_path_label = Label(root, textvariable=log_file_path_var, font=('Helvetica', 8), wraplength=450)
log_file_path_label.pack(pady=5)

# Buttons to open the log file and folder
open_log_button = Button(root, text="Open Log File", command=open_log_file, state=DISABLED, font=('Helvetica', 10))
open_log_button.pack(pady=5)

open_log_folder_button = Button(root, text="Open Log Folder", command=open_log_folder, state=DISABLED, font=('Helvetica', 10))
open_log_folder_button.pack(pady=5)

# Buttons for controlling the scan
start_button = Button(root, text="Start", command=start_scan, font=('Helvetica', 14))
stop_button = Button(root, text="Stop", command=stop_scan, font=('Helvetica', 14), state=DISABLED)

start_button.pack(pady=5)
stop_button.pack(pady=5)

# Button to select log folder
log_folder_button = Button(root, text="Select Log Folder", command=choose_log_folder, font=('Helvetica', 12))
log_folder_button.pack(pady=5)

# "About" Button
about_button = Button(root, text="About", command=open_about, font=('Helvetica', 12))
about_button.pack(side="left", anchor="sw", padx=10, pady=10)

# Function to open your website
def open_website(event):
    webbrowser.open_new("https://clement.business/")

# Footer with "Made by Clément GHANEME", clickable link
footer_label = Label(root, text="Made by Clément GHANEME", font=('Helvetica', 10), fg="blue", cursor="hand2")
footer_label.pack(side="right", anchor="se", padx=10, pady=10)
footer_label.bind("<Button-1>", open_website)

# Start the Tkinter GUI loop to show live progress
root.mainloop()

# Final log update for summary when stopping the scan
write_log_summary()

# Print log file save location
log_file = initialize_default_log_file()
print(f"Error log saved to: {log_file}")
