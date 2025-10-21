import os, re, argparse
from datetime import datetime
from collections import OrderedDict
import pandas as pd
from PyPDF2 import PdfReader

def extract_order_details(pdf_path):
    orders = []
    reader = PdfReader(pdf_path)
    delivery_section_pattern = re.compile(r'Online Ordering - (.*?)(?=Online Ordering|Guests|Expected Time)', re.DOTALL)
    phone_pattern = re.compile(r'\d{3}-\d{3}-\d{4}')
    name_pattern = re.compile(r'(?<!\S)([A-Za-z ,.\'-]+)(?=\n| \(|$)', re.DOTALL)
    address_pattern = re.compile(r'(\d{1,5}\s[\w\s,.]+(?:\n.*\w+,\s\w+\s\d{5}))', re.DOTALL)
    fallback_address_pattern = re.compile(r'([\w\s,.]+, \w+, \w+ \d{5})')
    email_pattern = re.compile(r'\S+@\S+')
    details_pattern = re.compile(r'\(detail\)')

    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue
        for section in delivery_section_pattern.findall(text):
            order = OrderedDict()
            m = name_pattern.search(section)
            order['Name'] = m.group().strip() if m else "Unknown Name"
            m = phone_pattern.search(section)
            if m:
                order['Phone'] = m.group()
            am = address_pattern.search(section) or fallback_address_pattern.search(section)
            if am and 'Phone' in order:
                address = am.group().strip()
                address = re.sub(order['Phone'], '', address)
                address = re.sub(order['Name'], '', address)
                address = re.sub(email_pattern, '', address)
                address = re.sub(details_pattern, '', address).strip()
                order['Address'] = ' '.join(address.split())
            if 'Phone' in order:
                orders.append(order)
    return orders

def main():
    p = argparse.ArgumentParser(description="Extract order details from a PDF and write to Excel.")
    p.add_argument("pdf_path", nargs="?", help="Input PDF (positional alternative to --input)")
    p.add_argument("--input", help="Input PDF path")
    p.add_argument("--output", help="Output Excel path")
    args = p.parse_args()

    pdf_in = args.input or args.pdf_path
    if not pdf_in:
        p.error("Provide PDF via positional arg or --input")

    orders = extract_order_details(pdf_in)
    df = pd.DataFrame(orders or [], columns=["Name","Phone","Address"])

    out_path = args.output
    if not out_path:
        # default next to input
        base = os.path.splitext(os.path.basename(pdf_in))[0]
        out_dir = os.path.dirname(pdf_in)
        out_path = os.path.join(out_dir, f"{base}_order_details_{datetime.now():%Y-%m-%d}.xlsx")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_excel(out_path, index=False)
    print(f"Saved: {out_path}", flush=True)

if __name__ == "__main__":
    main()