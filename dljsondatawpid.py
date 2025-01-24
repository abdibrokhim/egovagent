import os
import time
import json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_driver():
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.path.abspath("607ff4227b6428eee08802c0"),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def create_download_folder():
    folder_name = "607ff4227b6428eee08802c0"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

def wait_for_new_file(download_dir, existing_files, timeout=30):
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - existing_files
        if new_files:
            return max(new_files, key=lambda f: os.path.getctime(os.path.join(download_dir, f)))
        time.sleep(0.5)
    raise TimeoutError(f"No new file appeared in {download_dir} after {timeout} seconds")

def extract_path_id(container):
    try:
        link_element = container.find_element(By.CSS_SELECTOR, 'a.page-blue-title.cursor-pointer')
        href = link_element.get_attribute('href')
        parsed_path = urlparse(href).path
        return parsed_path.split('/')[-1]
    except Exception as e:
        print(f"Error extracting path_id: {str(e)}")
        return None

def download_json_files():
    BASE_URL = "https://data.egov.uz/eng/spheres/607ff4227b6428eee08802c0"
    PAGE_URL = BASE_URL + "?page={}"
    
    folder_name = create_download_folder()
    driver = setup_driver()
    
    try:
        for page_num in range(1, 104):
            print(f"Processing page {page_num}...")
            driver.get(PAGE_URL.format(page_num))
            time.sleep(2)  # Added sleep to ensure page loads
            
            try:
                WebDriverWait(driver, 20, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.list.d-flex.flex-column"))
                )
            except TimeoutException:
                print(f"Timeout waiting for page {page_num}")
                continue
            
            containers = driver.find_elements(By.CSS_SELECTOR, "div.list.d-flex.flex-column")
            time.sleep(2)  # Added sleep to ensure elements are loaded
            
            for container in containers:
                try:
                    # Extract path_id from the container
                    path_id = extract_path_id(container)
                    if not path_id:
                        continue
                    
                    # Find JSON download link within the container
                    links_div = container.find_element(By.CLASS_NAME, "links")
                    json_link = links_div.find_element(By.XPATH, ".//a[text()='json']")
                    
                    # Initiate download process
                    json_link.click()
                    time.sleep(2)  # Added sleep to ensure the click is registered
                    
                    # Handle modal dialog
                    WebDriverWait(driver, 20, 1).until(
                        EC.presence_of_element_located((By.ID, "modal"))
                    )
                    time.sleep(3)  # Added sleep to ensure modal is fully loaded
                    
                    # Handle checkbox
                    checkbox = driver.find_element(
                        By.XPATH, 
                        "//label[.//input[@value='60ae4b8bd47a196d52f26634']]"
                    )
                    checkbox.click()
                    time.sleep(2)  # Added sleep to ensure checkbox click is registered
                    
                    # Get existing files before download
                    existing_files = set(os.listdir(folder_name))
                    
                    # Click download button
                    download_button = driver.find_element(
                        By.XPATH, 
                        "//input[@value='Download dataset']"
                    )
                    download_button.click()
                    time.sleep(2)  # Added sleep to ensure download button click is registered
                    
                    # Wait for new file
                    try:
                        new_filename = wait_for_new_file(folder_name, existing_files)
                    except TimeoutError as e:
                        print(f"Download failed: {str(e)}")
                        continue
                    
                    # Modify JSON file
                    file_path = os.path.join(folder_name, new_filename)
                    time.sleep(2)  # Added sleep to ensure file is ready to be processed
                    try:
                        with open(file_path, 'r+', encoding='utf-8') as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                data.insert(0, {"path_id": path_id})
                                f.seek(0)
                                json.dump(data, f, ensure_ascii=False, indent=4)
                                f.truncate()
                            else:
                                print(f"Invalid JSON structure in {new_filename}")
                    except Exception as e:
                        print(f"Error processing {new_filename}: {str(e)}")
                    
                except Exception as e:
                    print(f"Error processing container: {str(e)}")
                    continue
            
            time.sleep(4)  # Added sleep to avoid overwhelming the server
    
    finally:
        driver.quit()
    
    print("All files processed successfully!")

if __name__ == "__main__":
    download_json_files()