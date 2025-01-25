import os
import time
import json
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

def setup_driver(fn):
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.path.abspath(fn),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def create_download_folder(fn):
    folder_name = fn
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

def download_json_files(fn, c):
    BASE_URL = f"https://data.egov.uz/eng/spheres/{fn}"
    PAGE_URL = BASE_URL + "?page={}"
    
    folder_name = create_download_folder(fn)
    driver = setup_driver(fn)
    
    try:
        for page_num in range(1, (c // 10) + 2):
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
    sphere_list = [
		{
			"guidId": "6076e30d7b6428eee08802aa",
			"title": {
				"engText": "Territory"
			},
			"structCount": 562,
            "status": "pending"
		},
		{
			"guidId": "607fe93e7b6428eee08802b0",
			"title": {
				"engText": "Economy"
			},
            "structCount": 3072,
			"status": "pending"
		},
		{
			"guidId": "607fea677b6428eee08802b1",
			"title": {
				"engText": "Healthcare"
			},
			"structCount": 692,
            "status": "pending"
		},
		{
			"guidId": "607fea9a7b6428eee08802b2",
			"title": {
				"engText": "Education"
			},
			"structCount": 757,
            "status": "done"
		},
		{
			"guidId": "607fed667b6428eee08802b3",
			"title": {
				"engText": "Culture"
			},
			"structCount": 67,
            "status": "pending"
		},
		{
			"guidId": "607fedbd7b6428eee08802b4",
			"title": {
				"engText": "Business"
			},
			"structCount": 147,
            "status": "pending"
		},
		{
			"guidId": "607feecc7b6428eee08802b5",
			"title": {
				"engText": "Real estate"
			},
			"structCount": 212,
            "status": "pending"
		},
		{
			"guidId": "607feffa7b6428eee08802b7",
			"title": {
				"engText": "SDG"
			},
			"structCount": 127,
            "status": "pending"
		},
		{
			"guidId": "607ff03a7b6428eee08802b8",
			"title": {
				"engText": "Tourism and sport"
			},
			"structCount": 49,
            "status": "done"
		},
		{
			"guidId": "607ff0997b6428eee08802b9",
			"title": {
				"engText": "Insurance"
			},
			"structCount": 4,
            "status": "done"
		},
		{
			"guidId": "607ff1137b6428eee08802ba",
			"title": {
				"engText": "Transportation"
			},
			"structCount": 155,
            "status": "pending"
		},
		{
			"guidId": "607ff2e57b6428eee08802bb",
			"title": {
				"engText": "Ecology"
			},
			"structCount": 155,
            "status": "pending"
		},
		{
			"guidId": "607ff3197b6428eee08802bc",
			"title": {
				"engText": "Population"
			},
			"structCount": 1520,
            "status": "pending"
		},
		{
			"guidId": "607ff3627b6428eee08802bd",
			"title": {
				"engText": "Finance"
			},
			"structCount": 1022,
            "status": "pending"
		},
		{
			"guidId": "607ff39e7b6428eee08802be",
			"title": {
				"engText": "Trade"
			},
			"structCount": 158,
            "status": "pending"
		},
		{
			"guidId": "607ff3e67b6428eee08802bf",
			"title": {
				"engText": "Offense"
			},
			"structCount": 40,
            "status": "done"
		},
		{
			"guidId": "607ff4227b6428eee08802c0",
			"title": {
				"engText": "Agriculture"
			},
			"structCount": 1028,
            "status": "done"
		},
		{
			"guidId": "607ff4557b6428eee08802c1",
			"title": {
				"engText": "ICT"
			},
			"structCount": 96,
            "status": "pending"
		},
		{
			"guidId": "607ff4ba7b6428eee08802c2",
			"title": {
				"engText": "Justice and judge"
			},
			"structCount": 24,
            "status": "done"
		}
	]

    guid_id = "607fea9a7b6428eee08802b2" # Education
    struct_count=757

    download_json_files(guid_id, struct_count)