import time
import pandas as pd
pd.set_option('display.max_colwidth', None)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException, TimeoutException


def setup_driver():
  try:
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=chrome_options)
  except Exception as e:
    print(f"Error setting up WebDriver: {e}")
    return None
  
def all_volume_of_year(driver, year):
  select_dropdown_option(driver, "year", year)
  volume_options = get_dropdown_options(driver, "volume")
  # print(f"Available volumes for year {year}:", volume_options)
  volume_options = [v for v in volume_options if not v.startswith("Select")]
  print(f"Filtered volumes for year {year}:", volume_options)
  return volume_options

def all_parts_of_year_and_volume(driver, year, volume):
  try:
    # Check if the part dropdown exists
    part_dropdown = driver.find_element(By.ID, "partno")
    if part_dropdown.is_displayed() and part_dropdown.is_enabled():
        select_dropdown_option(driver, "volume", volume)
        part_options = get_dropdown_options(driver, "partno")
        print("Available parts:", part_options)
        return part_options
    else:
      pass
        # print("Part dropdown exists but is not interactive.")
  except NoSuchElementException:
    print("Part dropdown not found for this year and volume.")
    return []

def all_years(driver):
  year_options = get_dropdown_options(driver, "year")
  year_options = [y for y in year_options if y.isdigit()]
  return year_options


def select_dropdown_option(driver, dropdown_id, option):
  try:
    dropdown = WebDriverWait(driver, 2).until(
        EC.element_to_be_clickable((By.ID, dropdown_id))
    )
    select = Select(dropdown)
    select.select_by_visible_text(option)
    WebDriverWait(driver, 3).until(
        EC.staleness_of(driver.find_element(By.TAG_NAME, 'body'))
    )
  except Exception as e:
    pass
      # print(f"Error selecting option '{option}' from dropdown '{dropdown_id}': {e}")

def get_dropdown_options(driver, dropdown_id):
  dropdown = WebDriverWait(driver, 2).until(
      EC.presence_of_element_located((By.ID, dropdown_id))
  )
  select = Select(dropdown)
  return [option.text for option in select.options]

def scrape_website(driver, year, volume, part=None):
  try:
    select_dropdown_option(driver, "year", year)
    select_dropdown_option(driver, "volume", volume)
    if part:
      try:
        part_dropdown = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, "partno"))
        )
        if part_dropdown.is_displayed() and part_dropdown.is_enabled():
          select_dropdown_option(driver, "partno", part)
        else:
          print("Part dropdown is not interactive.")
      except TimeoutException:
        print("Part dropdown not found for this year and volume.")

    # Wait for the page to load after selections
    WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "li.linumbr"))
    )
    return driver.page_source
  except Exception as e:
    print(f"Error in scrape_website: {e}")
    return None
  
def extract_case_data(driver):
  try:
    li_elements = driver.find_elements(By.CSS_SELECTOR, "li.linumbr")
    case_data = []
    for li in li_elements:
      try:
        parties = li.find_element(By.CSS_SELECTOR, "div.cite-data a").text
        case_num_date = li.find_elements(By.CSS_SELECTOR, "div.civil p")
        case_num = case_num_date[0].text if len(case_num_date) > 0 else "N/A"
        date = case_num_date[1].text if len(case_num_date) > 1 else "N/A"
        pdf_url = li.find_element(By.CSS_SELECTOR, "div.split > div.row a[href*='pdf']").get_attribute('href')

        case_data.append({
            "parties": parties,
            "case_number": case_num,
            "date": date,
            "pdf_url": pdf_url
        })
      except NoSuchElementException as e:
        print(f"Error extracting data from an element: {e}")
        continue

    return case_data

  except TimeoutException:
    print("Timeout waiting for elements to load")
    return []
  

def add_to_dataframe(all_case_data, all_case_df, year, volume, part=None):
  new_rows = []
  for case_detail in all_case_data:
    case_detail['year'] = year
    case_detail['volume'] = volume
    if part:
      case_detail['part'] = part
    new_rows.append(case_detail)

  new_df = pd.DataFrame(new_rows)
  return pd.concat([all_case_df, new_df], ignore_index=True)

def main(driver, year, volume, part=None):
  try:
    page_source = scrape_website(driver, year, volume, part)
    if page_source:
      case_data = extract_case_data(driver)
      print(f"Number of cases found: {len(case_data)}\n")
      return case_data
    else:
      print("Failed to scrape website")
      return []
  except Exception as e:
    print(f"An error occurred in main: {e}")
    return []

