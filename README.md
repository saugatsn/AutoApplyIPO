# AutoApplyIPO
This tool automatically applies for IPOs (Ordinary Shares). I generally apply to all ordinary shares, it's just that I keep forgetting. It's created to solve that problem.

## Overview
The program integrates with NepseUtils to automate the process of applying for IPOs. It's specifically written for applying to ordinary shares and runs invisibly in the background, logging activities for your review.

## Prerequisites
Before using this tool, you need to install and set up the following:
1. **NepseUtils**: This tool extends the functionality of NepseUtils.
   - Repository link: [https://github.com/arpandaze/nepseutils](https://github.com/arpandaze/nepseutils)
   - Follow the installation instructions in the NepseUtils repository
2. **AutoIt**: Required for automating the GUI interactions.
   - Download from: [https://www.autoitscript.com/site/autoit/downloads/](https://www.autoitscript.com/site/autoit/downloads/)

## Installation
1. Install NepseUtils by following the instructions in their repository and add your accounts as per that documentation
2. Install AutoIt using the link provided above
3. Create a folder where you want to store all the application files (e.g., a dedicated folder for this tool)
4. Copy the main.py file to this folder
5. Update the following in main.py:
   - Change the password in the `preloop` function 
   - Update the file paths at `BASE_DIR` where the log file and previously applied shares files will be saved

## AutoIt Script Setup
1. Open the `.au3` file in a text editor
2. Update the location in `$workingDir` where main.py is and where the log file will be saved
3. Save the file

## Building the Executable
1. Open the updated `.au3` file in the SciTE editor (included with AutoIt)
2. Click on "Tools" in the menu bar
3. Select "Build"
4. This will create an executable (`.exe`) file in the same directory

## Running the Application
1. Once the executable is created, run the `.exe` file
2. The application will automatically apply for IPOs of ordinary shares as they become available
3. Two log files are created:
   - `autoit_execution.log`: Records when the program was started and executed
   - `nepse_application.log`: Contains detailed information about IPO detection and application results

## How It Works
The program performs the following operations:
1. Checks if any ordinary shares are currently listed for IPO
2. If shares are found, it verifies if they have already been applied for by checking the `previously_applied_shares.json` file
3. If a share hasn't been applied for, it automatically applies with 10 units for all configured accounts
4. Records successful and failed applications, and saves this information to track previously applied shares
5. Shows a summary notification with the application results
6. Runs invisibly in the background, logging all activities for review

## Automatic Startup
To make the application run automatically when you start your computer:
1. Place only the `.exe` file in the Windows startup folder:
   - Press Win+R on your keyboard
   - Type `shell:startup` and press Enter
   - Copy the `.exe` file into this folder
2. The tool will now run in the background whenever you start your PC
3. It will automatically apply for shares and notify you if any new share is available and whether the application succeeded or failed

## Folder Organization
For best results, organize your files as follows:
- Create a dedicated folder for this application
- Keep all these files in the folder:
  - main.py
  - your .au3 script
  - nepse application log (will be generated)
  - autoit execution log (will be generated)
  - previously applied shares json (will be generated)
- Only the compiled .exe file should be placed in the startup folder

## Logs and Notifications
The program creates two log files to keep track of its activities:
1. `autoit_execution.log`: Records when the program runs, with timestamps
2. `nepse_application.log`: Contains detailed information about the application process

Additionally, a popup notification will display at the end of execution summarizing:
- Which shares were found
- Which shares were applied for
- Application success/failure status for each account
- Any errors that occurred
