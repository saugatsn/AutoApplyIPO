#!/usr/bin/python3

import argparse
import logging
from logging.handlers import RotatingFileHandler
import os
import time
import sys
import json
import tkinter as tk
from tkinter import messagebox
from cmd import Cmd
from getpass import getpass
from typing import List
from datetime import datetime
import atexit

from cryptography.fernet import InvalidToken
from tabulate import tabulate

from nepseutils.core.account import Account
from nepseutils.core.errors import LocalException
from nepseutils.core.meroshare import MeroShare
from nepseutils.core.portfolio import PortfolioEntry
from nepseutils.utils import config_converter

BASE_DIR = r'Your\Location\Here'

class TeeLogger:
    """A class that duplicates output to both a file and the original stream."""
    
    def __init__(self, filename, original_stream):
        # Change from 'a' (append) to 'w' (write) to overwrite previous log
        self.file = open(filename, 'w', encoding='utf-8')
        self.original_stream = original_stream
        
    def write(self, message):
        self.original_stream.write(message)
        self.file.write(message)
        self.file.flush()  # Make sure it's written immediately
        
    def flush(self):
        self.original_stream.flush()
        self.file.flush()
        
    def close(self):
        # Make sure to close the file
        if not self.file.closed:
            self.file.close()
    
    def __del__(self):
        # Ensure file is closed when object is garbage collected
        self.close()

# Set up regular logging
log_filename = os.path.join(BASE_DIR, 'nepse_application.log')
logging.basicConfig(filename=log_filename, filemode='w', level=logging.INFO,
                   format='%(asctime)s - %(message)s',
                   datefmt='%m/%d/%Y %I:%M:%S %p')  # Month/Day/Year 12-hour format with AM/PM
logging.getLogger("urllib3").setLevel(logging.ERROR)

# Set up console output redirection to also log to file
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = TeeLogger(log_filename, original_stdout)
sys.stderr = TeeLogger(log_filename, original_stderr)

class AutomatedNepseUtils(Cmd):
    prompt = "NepseUtils > "
    intro = "Welcome to NepseUtils! Type ? for help!"

    ms: MeroShare
    ordinary_shares = []
    current_share_index = 0
    application_summary = []
    previously_applied_file = os.path.join(BASE_DIR, 'previously_applied_shares.json')
    skip_popups_until_end = True  # Flag to control popup behavior

    def preloop(self, *args, **kwargs):
        if not (MeroShare.default_config_path()).exists():
            config_converter.pre_versioning_to_current()

            logging.info("Creating a new data file! Existing file not found!")

            MeroShare.default_config_directory().mkdir(parents=True, exist_ok=True)

            password = "PASSWORD HERE"  # Automatically enter password
            self.ms = MeroShare.new(password)

        else:
            # Wait for the prompt before entering password
            sys.stdout.write("Waiting for password prompt...\n")
            time.sleep(1)  # Give time for the prompt to appear
            
            password = "PASSWORD HERE"  # Automatically enter password
            
            try:
                self.ms = MeroShare.load(password)
                sys.stdout.write("Password entered successfully!\n")
            except InvalidToken as e:
                print("Incorrect password!")
                print(e)
                exit()
        
        # After successful login, automatically process the "apply" command
        time.sleep(1)  # Wait for the prompt to appear
        self.do_automated_apply("")

    def load_previously_applied_shares(self):
        """Load previously applied shares from JSON file"""
        if os.path.exists(self.previously_applied_file):
            try:
                with open(self.previously_applied_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error reading {self.previously_applied_file}, creating new one")
                return []
        return []

    def save_previously_applied_share(self, share_info):
        """Save applied share info to track previously applied shares"""
        previously_applied = self.load_previously_applied_shares()
        
        # Add new share info with timestamp
        share_record = {
            "scrip": share_info["scrip"],
            "name": share_info["name"],
            "close_date": share_info["close_date"],
            "applied_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "success_count": sum(1 for result in share_info['results'] if result['applied']),
            "failed_count": sum(1 for result in share_info['results'] if not result['applied'])
        }
        
        previously_applied.append(share_record)
        
        with open(self.previously_applied_file, 'w') as f:
            json.dump(previously_applied, f, indent=4)

    def is_share_previously_applied(self, scrip, close_date):
        """Check if a share has been previously applied based on scrip and close date"""
        previously_applied = self.load_previously_applied_shares()
        
        for share in previously_applied:
            if share["scrip"] == scrip and share["close_date"] == close_date:
                return True
                
        return False

    def help_add(self):
        print("Add a new account!")
        print("Usage: add {dmat} {password} {crn} {pin}")

    def do_add(self, args):
        args = args.split(" ")

        if len(args) == 4:
            dmat, password, crn, pin = args

        elif len(args) == 1 and args[0] == "":
            dmat = input("Enter DMAT: ")
            password = getpass(prompt="Enter Meroshare Password: ")

            if len(password) < 8:
                print("Password too short!")
                print("Pasting password on windows is not recommended!")
                return

            crn = input("Enter CRN Number: ")
            pin = input("Enter Meroshare PIN: ")

        else:
            print('Incorrect format. Type "help add" for help!')
            return

        capital_id = self.ms.capitals.get(dmat[3:8])

        if not capital_id:
            print("Could not find capital ID for given DMAT!")
            print("Updating capital list!")
            self.ms.update_capital_list()
            capital_id = self.ms.capitals.get(dmat[3:8])

        if not capital_id:
            print("Could not find capital ID for given DMAT!")
            print("Please enter capital ID manually!")
            capital_id = input("Enter Capital ID: ")

        account = Account(dmat, password, int(pin), int(capital_id), crn)

        try:
            account.get_details()
        except LocalException as e:
            print(f"Failed to obtain details for account: {e}")

        self.ms.accounts.append(account)
        self.ms.save_data()

        logging.info(f"Successfully obtained details for account: {account.name}")

    def help_remove(self):
        print("Remove an account!")
        print("Usage: remove")
        print("Then choose an account ID from the list!")

    def do_remove(self, args):
        self.do_list(args="accounts")
        account_id = input("Choose an account ID: ")
        del self.ms.accounts[int(account_id) - 1]
        self.ms.save_data()
        print("Account removed!")

    def list_accounts_full(self):
        print("WARNING: This will display password and pin of your accounts!")
        confirm = input("Do you want to continue? (y/n) :")

        if confirm == "y":
            headers = ["ID", "Name", "DMAT", "Account", "CRN", "Password", "PIN"]
            table = [
                [
                    self.ms.accounts.index(itm) + 1,
                    itm.name,
                    itm.dmat,
                    itm.account,
                    itm.crn,
                    itm.password,
                    itm.pin,
                ]
                for itm in self.ms.accounts
            ]
            print(tabulate(table, headers=headers, tablefmt="pretty"))

    def list_accounts(self):
        headers = ["ID", "Name", "DMAT", "Account", "CRN", "Tag"]
        table = [
            [
                self.ms.accounts.index(itm) + 1,
                itm.name,
                itm.dmat,
                itm.account,
                itm.crn,
                itm.tag,
            ]
            for itm in self.ms.accounts
        ]
        print(tabulate(table, headers=headers, tablefmt="pretty"))

    def list_results(self):
        results = self.ms.default_account.fetch_application_reports()

        headers = ["ID", "Scrip", "Name"]

        table = [
            [itm.get("companyShareId"), itm.get("scrip"), itm.get("companyName")]
            for itm in results[::-1]
        ]

        print(tabulate(table, headers=headers, tablefmt="pretty"))
        return results

    def list_capitals(self):
        headers = ["DPID", "ID"]
        table = [[key, value] for key, value in self.ms.capitals.items()]
        print(tabulate(table, headers=headers, tablefmt="pretty"))

    def help_portfolio(self):
        print("List portfolio of an account!")
        print("Usage: portfolio {account_id}")
        print("OR")
        print("Usage: portfolio all")

    def do_portfolio(self, args):
        portfolio: List[PortfolioEntry] = []

        if args == "all":
            for account in self.ms.accounts:
                if len(account.portfolio.entries) == 0:
                    account.fetch_portfolio()

                for entry in account.portfolio.entries:
                    found = False

                    for combined_entry in portfolio:
                        if combined_entry.script == entry.script:
                            combined_entry.current_balance += entry.current_balance
                            combined_entry.value_as_of_last_transaction_price += (
                                entry.value_as_of_last_transaction_price
                            )
                            combined_entry.value_as_of_previous_closing_price += (
                                entry.value_as_of_previous_closing_price
                            )
                            found = True
                            break

                    if not found:
                        portfolio.append(PortfolioEntry.from_json(entry.to_json()))

        else:
            self.list_accounts()
            account_id = input("Choose an account ID: ")

            account = self.ms.accounts[int(account_id) - 1]

            if len(account.portfolio.entries) == 0:
                account.fetch_portfolio()

            portfolio = account.portfolio.entries

        total_value = 0.0
        total_value_as_of_closing = 0.0
        for entry in portfolio:
            total_value += entry.value_as_of_last_transaction_price
            total_value_as_of_closing += entry.value_as_of_previous_closing_price

        headers = [
            "Scrip",
            "Balance",
            "Previous Closing Price",
            "Last Transaction Price",
            "Value as of Prev Closing",
            "Value",
            "+/- Amount",
            "+/- %",
        ]
        table = [
            [
                itm.script,
                itm.current_balance,
                f"{itm.previous_closing_price:,.1f}",
                f"{itm.last_transaction_price:,.1f}",
                f"{itm.value_as_of_previous_closing_price:,.1f}",
                f"{itm.value_as_of_last_transaction_price:,.1f}",
                f"{itm.value_as_of_last_transaction_price - itm.value_as_of_previous_closing_price:,.1f}",
                f"{(itm.value_as_of_last_transaction_price - itm.value_as_of_previous_closing_price)/itm.value_as_of_previous_closing_price*100:,.2f}%",
            ]
            for itm in portfolio
        ]
        total_diff = total_value - total_value_as_of_closing
        total_diff_percent = total_diff / total_value_as_of_closing * 100
        table.append(["Total", "", "","",f"{total_value_as_of_closing:,.1f}", f"{total_value:,.1f}", f"{total_diff:,.1f}", f"{total_diff_percent:,.2f}%"])
        print(tabulate(table, headers=headers, tablefmt="pretty"))

    def help_list(self):
        print("List accounts, capitals or results!")
        print("Usage: list { accounts | accounts full | capitals | results }")

    def do_list(self, args):
        args = args.split(" ")

        if not args:
            print('Incorrect format. Type "help list" for help!')
            return

        if len(args) == 2 and args[0] == "accounts" and args[1] == "full":
            return self.list_accounts_full()

        elif args[0] == "accounts":
            return self.list_accounts()

        elif args[0] == "capitals":
            return self.list_capitals()

        elif args[0] == "results":
            return self.list_results()

    def help_select(self):
        print("Selects accounts with specific tag to be used for further commands!")
        print("Usage: select {tag-name}")
        print("Usage: select all")

    def do_select(self, args):
        if not args:
            print('Incorrect format. Type "help select" for help!')
            return

        args = args.split(" ")

        if args == ["all"]:
            self.ms.tag_selections = []
            self.prompt = f"NepseUtils > "
            return
        else:
            self.ms.tag_selections = args
            self.prompt = f"NepseUtils ({','.join(self.ms.tag_selections)}) > "

    def help_sync(self):
        print("Syncs unfetched portfolio and application status from MeroShare!")

    def do_sync(self, args):
        for account in self.ms.accounts:
            account.fetch_portfolio()
            account.fetch_applied_issues()
            account.fetch_applied_issues_status()
            print(f"Synced {account.name}!")

    def help_stats(self):
        print("Shows statistics of accounts!")
        print("Usage: stats")

    def do_stats(self, args):
        headers = [
            "Name",
            "Total Applied",
            "Total Rejected",
            "Total Allocations",
            "Total Units Alloted",
            "Total Amount Alloted",
            "% Alloted",
        ]
        table = []

        for account in self.ms.accounts:
            account_applied = len(account.issues)
            account_alloted = 0
            account_rejected = 0
            account_units_alloted = 0.0
            account_amount_alloted = 0.0

            for issue in account.issues:
                if issue.alloted:
                    account_alloted += 1
                    account_units_alloted += issue.alloted_quantity or 0
                    account_amount_alloted += issue.applied_amount or 0

                if issue.status == "BLOCK_FAILED":
                    account_rejected += 1

            table.append(
                [
                    account.name,
                    account_applied,
                    account_rejected,
                    account_alloted,
                    account_units_alloted,
                    account_amount_alloted,
                    f"{account_alloted/account_applied*100:.2f}%",
                ]
            )

        total_applied = sum([itm[1] for itm in table])
        total_rejected = sum([itm[2] for itm in table])
        total_alloted = sum([itm[3] for itm in table])
        total_units_alloted = sum([itm[4] for itm in table])
        total_amount_alloted = sum([itm[5] for itm in table])
        total_percent_alloted = (
            total_alloted / total_applied * 100 if total_applied > 0 else 0.0
        )

        table.append(
            [
                "Total",
                total_applied,
                total_rejected,
                total_alloted,
                total_units_alloted,
                f"{total_amount_alloted:.2f}",
                f"{total_percent_alloted:.2f}%",
            ]
        )

        print(tabulate(table, headers=headers, tablefmt="pretty"))

    def do_result(self, args):
        if not args:
            self.do_list(args="results")
            company_id = input("Choose a company ID: ")
        else:
            args = args.split(" ")
            company_id = args[0]

        headers = ["Name", "Alloted", "Quantity"]
        table = []
        for account in self.ms.accounts:
            issue_ins = None
            for issue in account.issues:
                if issue.company_share_id == int(company_id):
                    issue_ins = issue
                    break

            if not issue_ins:
                table.append([account.name, "N/A", ""])
                continue

            if issue_ins.alloted == None:
                account.fetch_applied_issues_status(company_id=company_id)

            table.append(
                [
                    account.name,
                    "Yes" if issue_ins.alloted else "No",
                    "" if not issue_ins.alloted else issue_ins.alloted_quantity,
                ]
            )
        print(tabulate(table, headers=headers, tablefmt="pretty"))

    def do_tag(self, args):
        self.list_accounts()

        input_account_id = input("Choose an account ID: ")

        account = self.ms.accounts[int(input_account_id) - 1]

        tag = input(f"Set tag for account {account.name}: ")

        if tag == "" or tag == "all":
            tag = None
            print(f"Invalid tag {tag}. Setting to None")

        account.tag = tag
        self.ms.save_data()

    def help_tag(self):
        print("Tag an account to group them!")

    def help_result(self):
        print("Check results of IPO")

    def do_apply(self, args):
        company_to_apply = None
        quantity = None

        apply_headers = ["Name", "Quantity", "Applied", "Message"]
        apply_table = []

        appicable_issues = self.ms.default_account.fetch_applicable_issues()

        headers = [
            "Share ID",
            "Company Name",
            "Scrip",
            "Type",
            "Group",
            "Close Date",
        ]

        table = [
            [
                itm.get("companyShareId"),
                itm.get("companyName"),
                itm.get("scrip"),
                itm.get("shareTypeName"),
                itm.get("shareGroupName"),
                itm.get("issueCloseDate"),
            ]
            for itm in appicable_issues
        ]

        print(tabulate(table, headers=headers, tablefmt="pretty"))
        
        # Display ordinary shares separately
        ordinary_shares = [
            [
                itm.get("companyShareId"),
                itm.get("companyName"),
                itm.get("scrip"),
                itm.get("shareTypeName"),
                itm.get("shareGroupName"),
                itm.get("issueCloseDate"),
            ]
            for itm in appicable_issues if itm.get("shareGroupName") == "Ordinary Shares"
        ]
        
        if ordinary_shares:
            print("\nOrdinary Shares Available:")
            print(tabulate(ordinary_shares, headers=headers, tablefmt="pretty"))
            
            # Check if the first ordinary share has been previously applied
            if ordinary_shares:
                first_share_scrip = ordinary_shares[0][2]  # Scrip
                first_share_close_date = ordinary_shares[0][5]  # Close date
                
                if self.is_share_previously_applied(first_share_scrip, first_share_close_date):
                    print(f"\nShare {first_share_scrip} has already been applied for!")
                    # Add to summary but don't show popup yet
                    self.application_summary.append({
                        "id": ordinary_shares[0][0],
                        "name": ordinary_shares[0][1],
                        "scrip": first_share_scrip,
                        "type": ordinary_shares[0][3],
                        "group": ordinary_shares[0][4],
                        "close_date": first_share_close_date,
                        "previously_applied": True,
                        "results": []
                    })
                    
                    # Check if there are more ordinary shares to apply for
                    if len(ordinary_shares) > 1:
                        # Move to the next share
                        print("Moving to the next available share...")
                        company_to_apply = str(ordinary_shares[1][0])
                        print(f"Automatically selecting Share ID: {company_to_apply}")
                    else:
                        print("No more new shares to apply for.")
                        # Show final summary popup and exit
                        self.print_application_summary()
                        self.final_popup_and_exit()
                        return
                else:
                    # Automatically select the first ordinary share that hasn't been applied
                    company_to_apply = str(ordinary_shares[0][0])  # First ordinary share ID
                    print(f"Automatically selecting Share ID: {company_to_apply}")
        else:
            print("\nNo Ordinary Shares Available!")
            # Add this info to summary and show final popup
            self.application_summary.append({
                "no_shares": True,
                "message": "No ordinary shares available for application."
            })
            self.print_application_summary()
            self.final_popup_and_exit()
            return
        
        if not company_to_apply:
            company_to_apply = input("Enter Share ID: ")
        
        quantity = "10"  # Always apply for 10 units
        print(f"Units to Apply: {quantity}")

        # Record share information for summary
        share_info = None
        for share in appicable_issues:
            if str(share.get("companyShareId")) == company_to_apply:
                share_info = {
                    "id": share.get("companyShareId"),
                    "name": share.get("companyName"),
                    "scrip": share.get("scrip"),
                    "type": share.get("shareTypeName"),
                    "group": share.get("shareGroupName"),
                    "close_date": share.get("issueCloseDate"),
                    "results": []
                }
                break

        for account in self.ms.accounts:
            if not company_to_apply:
                appicable_issues = account.fetch_applicable_issues()

            try:
                result = account.apply(
                    share_id=int(company_to_apply), quantity=int(quantity)
                )
                application_status = result.get("status") == "CREATED"
                application_message = result.get("message")
            except Exception as e:
                print(e)
                print(f"Failed to apply for {account.name}!")
                application_status = False
                application_message = "Failed to apply!"
                result = {"status": "FAILED", "message": application_message}

            try:
                account.logout()
            except:
                print(f"Failed to logout for {account.name}!")

            apply_table.append(
                [
                    account.name,
                    quantity,
                    application_status,
                    application_message,
                ]
            )
            
            # Add to share info for summary
            if share_info:
                share_info["results"].append({
                    "account": account.name,
                    "applied": application_status,
                    "message": application_message
                })

        print(tabulate(apply_table, headers=apply_headers, tablefmt="pretty"))
        
        # Add to application summary
        if share_info:
            self.application_summary.append(share_info)
            
            # Save to previously applied shares
            self.save_previously_applied_share(share_info)
            
        # Check if there are more ordinary shares to apply for
        # If yes, exit to restart the process for the next share
        remaining_ordinary_shares = [
            share for share in appicable_issues 
            if share.get("shareGroupName") == "Ordinary Shares" 
            and str(share.get("companyShareId")) != company_to_apply
            and not self.is_share_previously_applied(share.get("scrip"), share.get("issueCloseDate"))
        ]
        
        if remaining_ordinary_shares:
            print("\nFound additional ordinary shares to apply for.")
            print("Exiting to restart for next share application...")
            self.print_application_summary(show_popup=False)  # Just print to terminal
            time.sleep(2)
            self.do_exit("")  # This will force the program to exit and restart
        else:
            print("\nNo more ordinary shares to apply for.")
            self.print_application_summary(show_popup=False)  # Just print to terminal
            self.final_popup_and_exit()  # Show final popup and exit

    def show_popup_message(self, title, message):
        """Show a popup message window"""
        try:
            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Show the message box
            messagebox.showinfo(title, message)
            
            # Destroy the root window
            root.destroy()
        except Exception as e:
            print(f"Failed to show popup: {e}")
            print(f"Popup message: {title} - {message}")

    def generate_summary_message(self):
        """Generate a formatted summary message for the popup"""
        if not self.application_summary:
            return "No shares were applied for."
            
        summary = "=== APPLICATION SUMMARY ===\n\n"
        
        for share in self.application_summary:
            if 'no_shares' in share and share['no_shares']:
                return share['message']
                
            if 'previously_applied' in share and share['previously_applied']:
                summary += f"Share: {share['name']} ({share['scrip']})\n"
                summary += f"Status: PREVIOUSLY APPLIED\n\n"
                continue
                
            summary += f"Share: {share['name']} ({share['scrip']})\n"
            summary += f"Type: {share['type']}\n"
            summary += f"Group: {share['group']}\n"
            
            success_count = sum(1 for result in share['results'] if result['applied'])
            failed_count = len(share['results']) - success_count
            
            summary += f"Application Status: {success_count} successful, {failed_count} failed\n"
            
            if failed_count > 0:
                summary += "Failed Applications:\n"
                for result in share['results']:
                    if not result['applied']:
                        summary += f"  - {result['account']}: {result['message']}\n"
            
            summary += "\n"
        
        return summary

    def print_application_summary(self, show_popup=False):
        """Print summary of all share applications and optionally show a popup"""
        if not self.application_summary:
            print("\n=== APPLICATION SUMMARY ===")
            print("No shares were applied for.")
            if show_popup:
                self.show_popup_message("Application Summary", "No shares were applied for.")
            return
            
        print("\n=== APPLICATION SUMMARY ===")
        for share in self.application_summary:
            if 'no_shares' in share and share['no_shares']:
                print(share['message'])
                continue
                
            if 'previously_applied' in share and share['previously_applied']:
                print(f"\nShare: {share['name']} ({share['scrip']})")
                print(f"Status: PREVIOUSLY APPLIED")
                continue
                
            print(f"\nShare: {share['name']} ({share['scrip']})")
            print(f"ID: {share['id']}")
            print(f"Type: {share['type']}")
            print(f"Group: {share['group']}")
            
            success_count = sum(1 for result in share['results'] if result['applied'])
            failed_count = len(share['results']) - success_count
            
            print(f"Application Status: {success_count} successful, {failed_count} failed")
            
            if failed_count > 0:
                print("Failed Applications:")
                for result in share['results']:
                    if not result['applied']:
                        print(f"  - {result['account']}: {result['message']}")
        
        print("\n=== END OF SUMMARY ===")
        
        # Show popup if requested
        if show_popup:
            summary_message = self.generate_summary_message()
            self.show_popup_message("Application Summary", summary_message)

    def final_popup_and_exit(self):
        """Display a final popup with complete summary and exit the program"""
        summary_message = self.generate_summary_message()
        
        try:
            # Create a hidden root window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Show the message box
            messagebox.showinfo("Application Complete", summary_message)
            
            # Destroy the root window
            root.destroy()
        except Exception as e:
            print(f"Failed to show final popup: {e}")
            print(f"Final popup message: {summary_message}")
        
        print("All processing complete. Exiting...")
        # Force exit to ensure the program closes
        os._exit(0)

    def do_automated_apply(self, args):
        """Automatically run the apply command"""
        time.sleep(1)  # Wait for the prompt
        print("Automatically running apply command...")
        self.do_apply("")

    def help_apply(self):
        print("Apply for shares")

    def do_status(self, args):
        company_share_id = None
        status_headers = ["Name", "Status", "Detail"]
        status_table = []
        for account in self.ms.accounts:
            reports = account.fetch_application_reports()

            if not company_share_id:
                headers = ["Share ID", "Company Name", "Scrip"]
                table = [
                    [
                        itm.get("companyShareId"),
                        itm.get("companyName"),
                        itm.get("scrip"),
                    ]
                    for itm in reports
                ]
                print(tabulate(table[::-1], headers=headers, tablefmt="pretty"))

                company_share_id = input("Enter Share ID: ")

            form_id = None
            for forms in reports:
                if forms.get("companyShareId") == int(company_share_id) and forms.get(
                    "applicantFormId"
                ):
                    form_id = forms.get("applicantFormId")
                    break

            try:
                detailed_form = account.fetch_application_status(form_id=form_id)
            except LocalException as e:
                account.logout()
                status_table.append([account.name, "N/A", "N/A"])
                continue

            account.logout()
            status_table.append(
                [
                    account.name,
                    detailed_form.get("statusName"),
                    detailed_form.get("reasonOrRemark"),
                ]
            )

        print(tabulate(status_table, headers=status_headers, tablefmt="pretty"))

    def do_change(self, args):
        args = args.split(" ")

        if args[0] == "lock":
            password = getpass(prompt="Enter new password for NepseUtils: ")
            self.ms.fernet = self.ms.fernet_init(password)
            self.ms.save_data()
            print("Password changed successfully!")
            exit(0)

        elif args[0] == "password":
            self.do_list(args="accounts")
            account_id = input("Choose an account ID: ")
            account = self.ms.accounts[int(account_id) - 1]

            new_password = getpass(
                prompt=f"Enter new password for account {account.name}: "
            )

            if len(new_password) < 8:
                print("Password too short!")
                print("Pasting password on windows is not recommended!")
                return

            self.ms.accounts[int(account_id) - 1].password = new_password
            self.ms.save_data()

    def help_loglevel(self):
        print("Set logging level")
        print("Usage: loglevel {debug | info | warning | error | critical}")

    def do_loglevel(self, args):
        if args == "debug":
            self.ms.logging_level = logging.DEBUG
        elif args == "info":
            self.ms.logging_level = logging.INFO
        elif args == "warning":
            self.ms.logging_level = logging.WARNING
        elif args == "error":
            self.ms.logging_level = logging.ERROR
        elif args == "critical":
            self.ms.logging_level = logging.CRITICAL
        else:
            print("Invalid argument!")

        self.ms.save_data()
        print(f"Logging level set to {args}! Restart NepseUtils!")
        exit()

    def help_change(self):
        print("Options:")
        print("lock: Change nepseutils password")

    def do_exit(self, *args):
        print("Bye")
        return True

    def help_exit(self):
        print("Exit NepseUtils. Shortcuts: q, or ctrl+D")

    def do_clear(self, args):
        os.system("cls" if os.name == "nt" else "clear")

    def help_telegram(self):
        print("Enable or disable telegram notifications")
        print("Usage: telegram {enable | disable}")

    def do_telegram(self, args):
        if args == "enable":
            token = input("Enter telegram bot token: ")
            chat_id = input("Enter telegram chat id: ")

            if not token or not chat_id:
                print("Invalid token or chat id!")
                return

            self.ms.telegram_bot_token = token
            self.ms.telegram_chat_id = chat_id
            self.ms.save_data()

        elif args == "disable":
            self.ms.telegram_bot_token = None
            self.ms.telegram_chat_id = None
            self.ms.save_data()

        else:
            print("Invalid argument!")

    def do_c(self, args):
        self.do_clear(args)

    def default(self, inp):
        if inp == "x" or inp == "q" or inp == "EOF":
            return self.do_exit(inp)

        print('Invalid command! Type "help" for help')

    def help_previously_applied(self):
        print("List previously applied shares")
        print("Usage: previously_applied")

    def do_previously_applied(self, args):
        """Display a list of previously applied shares"""
        previously_applied = self.load_previously_applied_shares()
        
        if not previously_applied:
            print("No previously applied shares found!")
            return
            
        headers = ["Scrip", "Company Name", "Close Date", "Applied Date", "Success", "Failed"]
        table = [
            [
                share["scrip"],
                share["name"],
                share["close_date"],
                share["applied_date"],
                share["success_count"],
                share["failed_count"]
            ]
            for share in previously_applied
        ]
        
        print(tabulate(table, headers=headers, tablefmt="pretty"))

    def help_clear_previously_applied(self):
        print("Clear the list of previously applied shares")
        print("Usage: clear_previously_applied")

    def do_clear_previously_applied(self, args):
        """Clear the list of previously applied shares"""
        if os.path.exists(self.previously_applied_file):
            confirm = input("Are you sure you want to clear all previously applied share records? (y/n): ")
            if confirm.lower() == "y":
                with open(self.previously_applied_file, 'w') as f:
                    json.dump([], f)
                print("Previously applied shares list cleared!")
            else:
                print("Operation cancelled.")
        else:
            print("No previously applied shares file found!")


def main():
    parser = argparse.ArgumentParser(description="Nepse Utility CLI")

    parser.add_argument("--password", help="Password for auto_apply")
    parser.add_argument("--auto", action="store_true", help="Enable auto_apply mode")

    args = parser.parse_args()

    if args.auto and args.password:
        AutomatedNepseUtils().auto(args.password)
    else:
        AutomatedNepseUtils().cmdloop()

# Add this after defining the TeeLogger class
def cleanup():
    if hasattr(sys.stdout, 'close') and not isinstance(sys.stdout, type(sys.__stdout__)):
        sys.stdout.close()
    if hasattr(sys.stderr, 'close') and not isinstance(sys.stderr, type(sys.__stderr__)):
        sys.stderr.close()


atexit.register(cleanup)


if __name__ == "__main__":
    main()
