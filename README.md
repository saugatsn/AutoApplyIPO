# AutoApplyIPO

This tool automatically applies for IPOs (Ordinary Shares). I generally apply to all ordinary shares, it's just that I keep forgetting. It's created to solve that problem.

## Overview

The program integrates with NepseUtils to automate the process of applying for IPOs. It's specifically written for applying to ordinary shares and runs invisibly in the background, logging activities for your review.

## Prerequisites

Before using this tool, you need to install and set up the following:

1. **NepseUtils**: This tool extends the functionality of NepseUtils.
   - Repository link: [https://github.com/arpandaze/nepseutils](https://github.com/arpandaze/nepseutils)
   - Follow the installation instructions in the NepseUtils repository

2. **AutoIt**: Required for automating the GUI interactions. (Optional/As per need)
   - Download from: [https://www.autoitscript.com/site/autoit/downloads/](https://www.autoitscript.com/site/autoit/downloads/)

## Installation

1. Install NepseUtils by following the instructions in their repository and add your accounts as per that documentation
2. Install AutoIt using the link provided above
3. Clone this repository to your local machine
4. Update the password in `main.py` to match the password you set up for NepseUtils (this is different from your MeroShare password)

## Building the Executable

1. Open the `.au3` file in the SciTE editor (included with AutoIt)
2. Click on "Tools" in the menu bar
3. Select "Build"
4. This will create an executable (`.exe`) file in the same directory

**Note**: Pre-built executable file is included in this repository. If you haven't made any changes to the `.au3` file, you can simply use these.

## Running the Application

1. Once the executable is created (or using the provided ones), simply run the `autoApplyShare.exe` file
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

1. Place both `autoApplyShare.exe` and `main.py` in the Windows startup folder:
   - Press Win+R on your keyboard
   - Type `shell:startup` and press Enter
   - Copy both files into this folder
2. The tool will now run in the background whenever you start your PC
3. It will automatically apply for shares and notify you if any new share is available and whether the application succeeded or failed

## Logs and Notifications

The program creates two log files to keep track of its activities:

1. `autoit_execution.log`: Records when the program runs, with timestamps in 12-hour format
2. `nepse_application.log`: Contains detailed information about the application process

Additionally, a popup notification will display at the end of execution summarizing:
- Which shares were found
- Which shares were applied for
- Application success/failure status for each account
- Any errors that occurred
