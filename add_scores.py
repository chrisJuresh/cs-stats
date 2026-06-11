import os
import re
import time
import csv

FILE_PATH = "master_stats.csv"

# The exact 15-column schema required by the app
HEADERS = [
    "Match ID", "Match Score", "Team", "Team Outcome", "Player", 
    "K", "D", "A", "Damage", "ADR", "ADR Differ...", "HLTV Rating 2.1", 
    "KAST, %", "Open kills", "Trade kills"
]

print("📝 Bare Match Stats Adder")
print("--------------------------------------------------")

# 1. Gather basic match details
team1_name = input("Enter Team 1 Name: ").strip()
team2_name = input("Enter Team 2 Name: ").strip()

while True:
    score_input = input(f"Enter the score from {team1_name}'s perspective (e.g., 13-7): ").strip()
    scores = [int(x) for x in re.findall(r'\d+', score_input)]
    if len(scores) == 2:
        t1_score, t2_score = scores[0], scores[1]
        break
    print("❌ Invalid score format. Please use something like '13-7' or '13:7'.")

# 2. Gather player names
print(f"\nEnter the players for {team1_name} (comma-separated, e.g.: chris, mark, daniel):")
t1_players = [p.strip() for p in input("> ").split(",") if p.strip()]

print(f"\nEnter the players for {team2_name} (comma-separated):")
t2_players = [p.strip() for p in input("> ").split(",") if p.strip()]

# 3. Determine Outcomes
if t1_score > t2_score:
    t1_outcome, t2_outcome = "Win", "Loss"
elif t1_score < t2_score:
    t1_outcome, t2_outcome = "Loss", "Win"
else:
    t1_outcome, t2_outcome = "Draw", "Draw"

# Generate a unique Match ID using a timestamp block
match_id = int(time.time() * 100)

rows_to_add = []

# Build rows for Team 1 (keeps entered score order)
for player in t1_players:
    row = [match_id, f"{t1_score}-{t2_score}", team1_name, t1_outcome, player] + [""] * 10
    rows_to_add.append(row)

# Build rows for Team 2 (automatically rotates score perspective)
for player in t2_players:
    row = [match_id, f"{t2_score}-{t1_score}", team2_name, t2_outcome, player] + [""] * 10
    rows_to_add.append(row)

# 4. Save to CSV file safely
file_exists = os.path.exists(FILE_PATH)

with open(FILE_PATH, mode='a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(HEADERS)
    writer.writerows(rows_to_add)

print("--------------------------------------------------")
print(f"🎉 Success! Generated Match ID {match_id} and added {len(rows_to_add)} bare player rows.")
print("Refresh your Streamlit app tab to see the updated records!")