FIRT - Clément GHANEME - 2024/09

The File Integrity & Readability Tester (FIRT) is a Python-based application designed for IT professionals and system administrators to assess file integrity across storage devices. 

It systematically scans a specified drive or directory, using multi-threading to maintain a responsive user interface while testing each file's readability. 
For each file, the application spawns a thread to execute a read operation within a user-defined timeout period. 
The read process involves attempting to open the file in binary mode and read its contents. 
If the file can be successfully read within the allotted time, it is marked as readable. 
If the operation times out or encounters an error, the file is logged as unreadable or skipped, and the exact error 
(e.g., permission denied, corrupted sectors) is documented in the log file. This design ensures the application can handle a large number of files, including those on potentially damaged or corrupted storage media, without freezing or becoming unresponsive.

The application employs Tkinter for its graphical user interface, providing real-time updates on scan progress, including total files processed, remaining files, read failures, and skipped files. 
The UI supports different scan modes (full drive or specific directory) and allows configuration of scan parameters like the timeout duration. 
Results are logged in real-time to a text file, including detailed error messages and a summary of the scan's outcome. 

Ex.Log. -----------

Error reading C:\DumpStack.log: [Errno 13] Permission denied: 'C:\\DumpStack.log'
Error reading C:\DumpStack.log.tmp: [Errno 13] Permission denied: 'C:\\DumpStack.log.tmp'
Error reading C:\pagefile.sys: [Errno 13] Permission denied: 'C:\\pagefile.sys'
Error reading C:\swapfile.sys: [Errno 13] Permission denied: 'C:\\swapfile.sys'
Path scanned: C:\

Summary:
Total files scanned: 7757
Readable files: 7752
Unreadable files: 4
Skipped files: 0
Time taken: 0:02:18

-----------

This log file's path is configurable and defaults to the script's directory if not specified. 
Upon completion or user interruption, the app finalizes the scan, writes a summary to the log, and can reset itself by restarting the entire process through the subprocess module.

This software was developed to address a common issue in IT environments where standard tools fail to identify specific corrupted or unreadable files. 
Often, backup processes encounter errors due to corrupted sectors that go unnoticed by tools like SMART checks. 
After a partial backup or data recovery, it can be challenging to pinpoint which files were lost or corrupted. 
FIRT was created to fill this gap, offering a detailed analysis of file integrity to ensure no critical data is overlooked during backups or transfers.

Disclaimer: This software is provided 'as is' without any guarantees or warranty. 
While it is designed to aid in assessing file integrity and readability, I cannot be held responsible for any loss, damage, or data corruption that may occur through its use. 
Users are advised to exercise caution and ensure they have proper backups before using this tool on critical systems.
