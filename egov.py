import requests
import json

def get_sphere_list():
    api_url = "https://data.egov.uz/apiClient/Main/GetSphereList?hasAral=false"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        # save the data to a file
        file_name = "sphere_list.json"
        with open(file_name, "w") as file:
            json.dump(data, file)
        print(f"Data saved to {file_name}")
    else:
        print("Failed to retrieve data:", response.status_code)


if __name__ == "__main__":
    get_sphere_list()