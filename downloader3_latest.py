import os
import pandas as pd
import requests
from urllib.parse import urlparse
import re
import csv
from datetime import datetime

year_list = ["2002","2001","2000"]
current_dir = os.getcwd()

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

def download_file(url, save_path):
    try:
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {save_path}")
        return True
    except requests.RequestException as e:
        print(f"Failed to download: {url}. Error: {e}")
    except IOError as e:
        print(f"Failed to save file: {save_path}. Error: {e}")
    return False

def create_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as e:
        print(f"Failed to create folder: {path}. Error: {e}")

def log_failed_download(csv_path, year, volume, part, parties, pdf_url):
    try:
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['timestamp', 'year', 'volume', 'part', 'parties', 'pdf_url']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'year': year,
                'volume': volume,
                'part': part,
                'parties': parties,
                'pdf_url': pdf_url
            })
        print(f"Logged failed download to: {csv_path}")
    except Exception as e:
        print(f"Error logging failed download: {e}")

# Create the not_downloaded_data directory
not_downloaded_dir = os.path.join(current_dir, "not_downloaded_data")
create_folder(not_downloaded_dir)

# Create or open the CSV file for logging failed downloads
failed_downloads_csv = os.path.join(not_downloaded_dir, "failed_downloads.csv")

# Ensure the CSV file exists with headers
if not os.path.isfile(failed_downloads_csv):
    with open(failed_downloads_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'year', 'volume', 'part', 'parties', 'pdf_url'])
    print(f"Created new CSV file: {failed_downloads_csv}")

for y in year_list:
    try:
        relative_csv_path = os.path.join("files", f"data_for_{y}.csv")
        csv_data_path = os.path.join(current_dir, relative_csv_path)

        relative_download_path = os.path.join("downloaded_judgments", str(y))
        year_folder = os.path.join(current_dir, relative_download_path)
        create_folder(year_folder)

        pd_data = pd.read_csv(csv_data_path)
        unique_volumes = pd_data["volume"].unique()

        for v in unique_volumes:
            volume_folder = os.path.join(year_folder, f"{v}")
            create_folder(volume_folder)

            volume_data = pd_data[pd_data["volume"] == v]
            unique_parts = volume_data["part"].unique()

            if pd.isna(unique_parts).any():
                for _, row in volume_data.iterrows():
                    try:
                        pdf_url = row["pdf_url"]
                        parties = sanitize_filename(row["parties"])
                        print(f"Processing: year: {y}, volume: {v}, pdf_url: {pdf_url}")
                        file_extension = ".pdf"
                        filename = f"{parties}{file_extension}"
                        save_path = os.path.join(volume_folder, filename)
                        if not download_file(pdf_url, save_path):
                            log_failed_download(failed_downloads_csv, y, v, "N/A", parties, pdf_url)
                    except Exception as e:
                        print(f"Error processing row: {e}")
                        log_failed_download(failed_downloads_csv, y, v, "N/A", parties, pdf_url)
            else:
                for p in unique_parts:
                    part_folder = os.path.join(volume_folder, f"{p}")
                    create_folder(part_folder)

                    part_data = volume_data[volume_data["part"] == p]
                    for _, row in part_data.iterrows():
                        try:
                            pdf_url = row["pdf_url"]
                            parties = sanitize_filename(row["parties"])
                            print(f"Processing: year: {y}, volume: {v}, part: {p}, pdf_url: {pdf_url}")
                            file_extension = ".pdf"
                            filename = f"{parties}{file_extension}"
                            save_path = os.path.join(part_folder, filename)
                            if not download_file(pdf_url, save_path):
                                log_failed_download(failed_downloads_csv, y, v, p, parties, pdf_url)
                        except Exception as e:
                            print(f"Error processing row: {e}")
                            log_failed_download(failed_downloads_csv, y, v, p, parties, pdf_url)
    except Exception as e:
        print(f"Error processing year {y}: {e}")

print(f"Script completed. Check {failed_downloads_csv} for any failed downloads.")