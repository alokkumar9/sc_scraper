import os
from tqdm import tqdm
import re

from modules import*


if __name__ == "__main__":
  driver = setup_driver()
  if driver:
    try:
      driver.get("https://digiscr.sci.gov.in/")
      WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
      all_years = ["1969", "1968", "1967", "1966", "1965", "1964", "1963", "1962", "1961", "1960", "1959", "1958", "1957", "1956", "1955", "1954", "1953", "1952", "1951", "1950"]
 # Add more years if needed
      try:
        for year in all_years:
          all_case_df = pd.DataFrame(columns=['year', 'volume', 'part', 'parties', 'case_number', 'date', 'pdf_url'])
          volumes = all_volume_of_year(driver, year)
          for volume in volumes:
            print(f"Volume: {volume}")
            part_options = all_parts_of_year_and_volume(driver, year, volume)
            if part_options:
              for part in part_options:
                print(f"Part: {part}")
                all_case_data = main(driver, year, volume, part)
                all_case_df = add_to_dataframe(all_case_data, all_case_df, year, volume, part)
            else:
              all_case_data = main(driver, year, volume)
              all_case_df = add_to_dataframe(all_case_data, all_case_df, year, volume)

          # You might want to save the DataFrame here
          current_dir = os.path.dirname(os.path.abspath(__file__))
          files_dir = os.path.join(current_dir, 'files')
          if not os.path.exists(files_dir):
            os.makedirs(files_dir)
          file_path = os.path.join(files_dir, f'data_for_{year}.csv')
          all_case_df.to_csv(file_path, index=False)

      except Exception as e:
        print(f"failed for {year}, and {volume} , ERROR: {e}")
    finally:
        driver.quit()
  else:
      print("Failed to set up WebDriver. Exiting.")