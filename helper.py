import os

def count_json_files(folder='607ff3e67b6428eee08802bf'):
    json_files = [f for f in os.listdir(folder) if f.endswith('.json')]
    return len(json_files)

if __name__ == "__main__":
    l = count_json_files()
    print(l)