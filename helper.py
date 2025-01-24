import os
import json

def transform_json_files(folder='607ff4227b6428eee08802c0'):
    json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
    for json_file in json_files:
        file_path = os.path.join(folder, json_file)

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract path_id from the first object
        path_id = data[0].pop("path_id", None)

        # Create a new list where each dict includes the path_id
        transformed_data = []
        for index, obj in enumerate(data[1:], start=1):
            obj["path_id"] = path_id
            obj["ID"] = str(index)  # Assign sequential ID starting from 1
            transformed_data.append(obj)
        
        # Overwrite the original file with the transformed data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=4, ensure_ascii=False)
    
    print(f"Transformation complete. Files in the '{folder}' folder have been updated.")

def count_json_files(folder='607ff3e67b6428eee08802bf'):
    json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
    return len(json_files)

if __name__ == "__main__":
    l = count_json_files()
    print(l)

    # Test the functions
    # transform_json_files()
    # print(f"Number of .json files in the folder: {count_json_files()}")
