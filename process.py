import os
import csv
import json
import glob
import shutil

os.makedirs('matches', exist_ok=True)
os.makedirs('processed', exist_ok=True)

ALIASES_FILE = 'aliases.json'
MASTER_FILE = 'master_stats.csv'

# Load our player name memory (aliases)
if os.path.exists(ALIASES_FILE):
    with open(ALIASES_FILE, 'r', encoding='utf-8') as f:
        aliases = json.load(f)
else:
    aliases = {}

csv_files = glob.glob('matches/*.csv')

if not csv_files:
    print("No CSV files found in the 'matches' folder.")
    exit()

master_data = []
headers = []

# Process each file
for file in csv_files:
    with open(file, 'r', encoding='utf-8') as f:
        reader = list(csv.reader(f))
        if len(reader) <= 1: 
            continue 
        
        # Grab headers from the first file
        if not headers:
            headers = reader[0]

        print(f"Processing {os.path.basename(file)}...")

        # Clean the player rows (Player Name is now at index 3)
        for row in reader[1:]:
            if not row: continue
            player_name = row[3]

            # If we haven't seen this player before, ask who it is
            if player_name not in aliases:
                print(f"  New player detected: '{player_name}'")
                real_name = input(f"  Who is this actually? (Press Enter to keep '{player_name}'): ").strip()
                
                if real_name == "":
                    aliases[player_name] = player_name
                else:
                    aliases[player_name] = real_name

            # Swap the weird username for the clean, real one
            row[3] = aliases[player_name]
            master_data.append(row)

    # Move the file to the processed folder
    shutil.move(file, os.path.join('processed', os.path.basename(file)))

# Save our newly learned aliases
with open(ALIASES_FILE, 'w', encoding='utf-8') as f:
    json.dump(aliases, f, indent=4)

# Append all the new data to the master CSV
file_exists = os.path.exists(MASTER_FILE)
with open(MASTER_FILE, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(headers)
    writer.writerows(master_data)

print(f"\nSuccess! Processed {len(csv_files)} files into {MASTER_FILE}.")