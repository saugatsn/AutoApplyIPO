# AutoApplyIPO

This tool automatically applies for IPOs (Ordinary Shares). We generally apply to all ordinary shares, it's just that we keep forgetting. It's created to solve that problem.

## Overview

The program integrates with NepseUtils to automate the process of applying for IPOs. It's designed to work specifically with ordinary shares.

## Prerequisites

Before using this tool, you need to install and set up the following:

1. **NepseUtils**: This tool extends the functionality of NepseUtils.
   - Repository link: [https://github.com/arpandaze/nepseutils](https://github.com/arpandaze/nepseutils)
   - Follow the installation instructions in the NepseUtils repository

2. **AutoIt**: Required for automating the GUI interactions.
   - Download from: [https://www.autoitscript.com/site/autoit/downloads/](https://www.autoitscript.com/site/autoit/downloads/)

## Installation

1. Clone this repository to your local machine
2. Install NepseUtils by following the instructions in their repository
3. Install AutoIt using the link provided above

## Configuration

1. Open the `.au3` file in any text editor or the SciTE editor (included with AutoIt)
2. Locate the section where the NepseUtils password is entered
3. Replace the default password with your NepseUtils password
4. Save the file

## Building the Executable

1. Open the `.au3` file in the SciTE editor
2. Click on "Tools" in the menu bar
3. Select "Build"
4. This will create an executable (.exe) file in the same directory

## Running the Application

1. Once the executable is created, simply run the `main.exe` file
2. The application will automatically apply for IPOs of ordinary shares as they become available

## Automatic Startup

To make the application run automatically when you start your computer:

1. Place both `main.exe` and `applyShare.exe` in the Windows startup folder:
   - Press `Win+R` on your keyboard
   - Type `shell:startup` and press Enter
   - Copy both files into this folder

2. The tool will now run in the background whenever you start your PC
3. It will automatically apply for shares and notify you if any new share is available and whether the application succeeded or failed
