import os
import re
import pandas as pd
import argparse
from datetime import datetime
from PyPDF2 import PdfReader
from collections import OrderedDict

def extract_order_details(pdf_path):
    # Initialize a list to store orders
    orders = []

    # Open the PDF
    reader = PdfReader(pdf_path)
    num_pages = len(reader.pages)

    # Regex patterns to extract relevant information
    delivery_section_pattern = re.compile(r'Online Ordering - (.*?)(?=Online Ordering|Guests|Expected Time)', re.DOTALL)
    phone_pattern = re.compile(r'\d{3}-\d{3}-\d{4}')
    ##name_pattern = re.compile(r'([A-Za-z]+\s[A-Za-z]+)(?=\n| \()', re.DOTALL)  # Match first and last name
    #name_pattern = re.compile(r'([A-Za-z ,.\'-]+)(?=\n| \()', re.DOTALL)  # Match the full name with spaces and common punctuation
    name_pattern = re.compile(r'(?<!\S)([A-Za-z ,.\'-]+)(?=\n| \(|$)', re.DOTALL)

    address_pattern = re.compile(r'(\d{1,5}\s[\w\s,.]+(?:\n.*\w+,\s\w+\s\d{5}))', re.DOTALL)
    fallback_address_pattern = re.compile(r'([\w\s,.]+, \w+, \w+ \d{5})')
    email_pattern = re.compile(r'\S+@\S+')  # Matches email addresses
    details_pattern = re.compile(r'\(detail\)')  # Matches "(detail)" text

    # Loop through all pages
    for page_num in range(num_pages):
        page = reader.pages[page_num].extract_text()

        # Find all delivery sections
        delivery_sections = delivery_section_pattern.findall(page)

        for section in delivery_sections:
            order = OrderedDict()

            # Extract name (ensure it captures only names and ignores other fields)
            name_match = name_pattern.search(section)
            if name_match:
                order['Name'] = name_match.group().strip()
            else:
                order['Name'] = "Unknown Name"

            # Extract phone number
            phone_match = phone_pattern.search(section)
            if phone_match:
                order['Phone'] = phone_match.group()

            # Try extracting the address using the primary pattern
            address_match = address_pattern.search(section)
            if not address_match:
                # If the primary pattern fails, try the fallback pattern
                address_match = fallback_address_pattern.search(section)

            if address_match:
                address = address_match.group().strip()

                # Remove phone number, name, emails, and details from the address
                address = re.sub(order['Phone'], '', address)  # Remove phone number from address
                address = re.sub(order['Name'], '', address)  # Remove name from address
                address = re.sub(email_pattern, '', address)  # Remove email addresses
                address = re.sub(details_pattern, '', address).strip()  # Remove "(detail)"

                # Clean up extra spaces or line breaks
                order['Address'] = ' '.join(address.split())

            # Append the order details to the list if name and phone are found
            if 'Phone' in order:
                orders.append(order)

    return orders

def main():
    # Setup argument parser
    parser = argparse.ArgumentParser(description="Extract order details from a PDF file and save to Excel.")
    parser.add_argument("pdf_path", help="Path to the PDF file to process")

    args = parser.parse_args()

    # Extract order details
    order_details = extract_order_details(args.pdf_path)

    # Check if any orders were extracted
    if not order_details:
        print("No order details were extracted from the PDF.")
        return

    # Convert the list of orders into a pandas DataFrame
    df = pd.DataFrame(order_details)

    # Get the current date and format it as YYYY-MM-DD
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Create the output folder if it does not exist
    output_folder = "output"
    os.makedirs(output_folder, exist_ok=True)

    # Set the output Excel path
    output_excel_path = os.path.join(output_folder, f"order_details_{current_date}.xlsx")

    # Save the DataFrame to an Excel file in the output folder
    df.to_excel(output_excel_path, index=False)

    print(f"Order details saved to {output_excel_path}")

if __name__ == "__main__":
    main()
