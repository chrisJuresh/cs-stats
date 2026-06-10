import os
import re
import pandas as pd
import plotly.express as px
import streamlit as st

# Configure the web page
st.set_page_config(page_title="CS2 Team Analytics", layout="wide", page_icon="📊")

st.title("📊 The Ultimate CS2 Master Leaderboard")
st.markdown("---")

def process_match_results(df):
    """
    Infers Win/Loss, Rounds Won, and Rounds Lost by assigning 
    the highest score to the team with the most total kills.
    """
    rounds_won_list = []
    rounds_lost_list = []
    result_list = []
    
    for idx, row in df.iterrows():
        match_id = row['Match ID']
        team = row['Team']
        score_str = str(row['Match Score'])
        
        match_df = df[df['Match ID'] == match_id]
        team_kills = match_df.groupby('Team')['K'].sum()
        
        try:
            scores = [int(x) for x in re.findall(r'\d+', score_str)]
            if len(scores) >= 2:
                max_score = max(scores[0], scores[1])
                min_score = min(scores[0], scores[1])
                
                if max_score == min_score:
                    result_list.append('Draw')
                    rounds_won_list.append(max_score)
                    rounds_lost_list.append(max_score)
                else:
                    if winning_team := team if team_kills.empty else team_kills.idxmax():
                        pass
                        
                    if team == winning_team:
                        result_list.append('Win')
                        rounds_won_list.append(max_score)
                        rounds_lost_list.append(min_score)
                    else:
                        result_list.append('Loss')
                        rounds_won_list.append(min_score)
                        rounds_lost_list.append(max_score)
            else:
                result_list.append('Unknown')
                rounds_won_list.append(0)
                rounds_lost_list.append(0)
        except Exception:
            result_list.append('Unknown')
            rounds_won_list.append(0)
            rounds_lost_list.append(0)
            
    df['Result'] = result_list
    df['Rounds Won'] = rounds_won_list
    df['Rounds Lost'] = rounds_lost_list
    return df

# Check if the master data file exists
if not os.path.exists("master_stats.csv"):
    st.error("🔴 'master_stats.csv' not found! Make sure to run your data processing script first.")
else:
    # Load the data
    df = pd.read_csv("master_stats.csv")
    
    # Clean and standardize all numeric columns
    numeric_cols = ['K', 'D', 'A', 'Damage', 'ADR', 'HLTV Rating 2.1', 'KAST, %', 'Open kills', 'Trade kills']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    if 'ADR Differ...' in df.columns:
        df['ADR Differ...'] = pd.to_numeric(df['ADR Differ...'].astype(str).str.replace('+', '', regex=False), errors='coerce')

    # Run win/loss/round calculation engine
    df = process_match_results(df)

    # 1. DATA AGGREGATION
    base_metrics = df.groupby('Player').agg({
        'Match ID': 'count',
        'KAST, %': ['mean', 'std'],
        'ADR': ['mean', 'std'],
        'ADR Differ...': ['mean', 'std'],
        'K': ['sum', 'mean', 'std'],
        'Open kills': ['sum', 'mean', 'std'],
        'D': ['sum', 'mean', 'std'],
        'A': ['sum', 'mean', 'std'],
        'Damage': ['sum', 'mean', 'std'],
        'Trade kills': ['sum', 'mean', 'std'],
        'Rounds Won': ['sum', 'mean', 'std'],
        'Rounds Lost': ['sum', 'mean', 'std'],
        'HLTV Rating 2.1': ['mean', 'std']
    })
    
    # Flatten names cleanly
    base_metrics.columns = ['_'.join(col).strip() for col in base_metrics.columns.values]
    leaderboard = base_metrics.reset_index()
    
    # Map Match Outcomes safely
    unique_players = leaderboard['Player'].tolist()
    wins_map = df[df['Result'] == 'Win'].groupby('Player')['Match ID'].count().reindex(unique_players, fill_value=0).values
    losses_map = df[df['Result'] == 'Loss'].groupby('Player')['Match ID'].count().reindex(unique_players, fill_value=0).values
    draws_map = df[df['Result'] == 'Draw'].groupby('Player')['Match ID'].count().reindex(unique_players, fill_value=0).values
    
    leaderboard['Games Won'] = wins_map
    leaderboard['Games Lost'] = losses_map
    leaderboard['Games Drawn'] = draws_map

    # Calculate Advanced Derived Statistics
    leaderboard['Win Rate %'] = ((leaderboard['Games Won'] / leaderboard['Match ID_count']) * 100).round(1)
    leaderboard['Total Rounds Played'] = leaderboard['Rounds Won_sum'] + leaderboard['Rounds Lost_sum']
    leaderboard['Round Win Rate %'] = ((leaderboard['Rounds Won_sum'] / leaderboard['Total Rounds Played']) * 100).round(1)
    leaderboard['K/D Ratio'] = (leaderboard['K_sum'] / leaderboard['D_sum']).round(2)

    # Map internally to structured display columns
    final_column_mapping = {
        'Player': 'Player',
        'Match ID_count': 'Matches Played',
        'Games Won': 'Games Won',
        'Games Lost': 'Games Lost',
        'Games Drawn': 'Games Drawn',
        'Win Rate %': 'Win Rate %',
        'Total Rounds Played': 'Total Rounds Played',
        'Rounds Won_sum': 'Total Rounds Won',
        'Rounds Lost_sum': 'Total Rounds Lost',
        'Round Win Rate %': 'Round Win Rate %',
        'KAST, %_mean': 'Avg KAST %',
        'ADR_mean': 'Avg ADR',
        'ADR Differ..._mean': 'Avg ADR Diff',
        'K_mean': 'Avg Kills',
        'K_sum': 'Total Kills',
        'Open kills_mean': 'Avg Open Kills',
        'Open kills_sum': 'Total Open Kills',
        'D_mean': 'Avg Deaths',
        'D_sum': 'Total Deaths',
        'Damage_mean': 'Avg Damage',
        'Damage_sum': 'Total Damage',
        'A_mean': 'Avg Assists',
        'A_sum': 'Total Assists',
        'Trade kills_mean': 'Avg Trade Kills',
        'Trade kills_sum': 'Total Trade Kills',
        'Rounds Won_mean': 'Avg Rounds Won',
        'Rounds Lost_mean': 'Avg Rounds Lost',
        'HLTV Rating 2.1_mean': 'Avg Rating',
        # Standard deviations mapped behind the scenes for error bars
        'KAST, %_std': 'Std KAST %',
        'ADR_std': 'Std ADR',
        'ADR Differ..._std': 'Std ADR Diff',
        'K_std': 'Std Kills',
        'Open kills_std': 'Std Open Kills',
        'D_std': 'Std Deaths',
        'A_std': 'Std Assists',
        'Damage_std': 'Std Damage',
        'Trade kills_std': 'Std Trade Kills',
        'Rounds Won_std': 'Std Rounds Won',
        'Rounds Lost_std': 'Std Rounds Lost',
        'HLTV Rating 2.1_std': 'Std Rating'
    }
    
    leaderboard = leaderboard.rename(columns=final_column_mapping)

    # Standardize rounding formatting
    for col in ['Avg KAST %', 'Avg ADR', 'Avg ADR Diff', 'Avg Kills', 'Avg Open Kills', 'Avg Deaths', 'Avg Assists', 'Avg Trade Kills', 'Avg Rounds Won', 'Avg Rounds Lost', 'Avg Rating']:
        leaderboard[col] = leaderboard[col].round(1) if col != 'Avg Rating' else leaderboard[col].round(2)
    leaderboard['Avg Damage'] = leaderboard['Avg Damage'].round(0)

    # Sort master table precisely by your specified core performance weights
    leaderboard = leaderboard.sort_values(by=['Avg KAST %', 'Avg ADR', 'Avg Kills'], ascending=[False, False, False])

    # Display Master Metrics Data Grid Matrix
    st.subheader("📋 Complete Master Analytics Grid")
    st.write("Scroll horizontally to examine all metrics simultaneously.")
    
    # Custom exact requested structured table index alignment ordering logic
    table_display_order = [
        'Player', 'Matches Played', 'Games Won', 'Games Lost', 'Games Drawn', 'Win Rate %',
        'Total Rounds Played', 'Total Rounds Won', 'Total Rounds Lost', 'Round Win Rate %',
        'Avg KAST %', 
        'Avg ADR', 'Avg ADR Diff', 
        'Avg Kills', 'Total Kills', 
        'Avg Open Kills', 'Total Open Kills', 
        'Avg Deaths', 'Total Deaths', 
        'Avg Assists', 'Total Assists', 'Avg Damage', 'Total Damage',
        'Avg Trade Kills', 'Total Trade Kills', 'Avg Rounds Won', 'Avg Rounds Lost',
        'Avg Rating'
    ]
    st.dataframe(leaderboard[table_display_order], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📈 All Performance Charts")
    st.caption("*Error bars display standard deviation (consistency metric). Single match entries show no error bars.*")

    # Complete metric chart deployment sequence arranged by exact weight of your specification
    metrics_to_chart = [
        ("Avg KAST %", "Std KAST %", "1. Round Contribution: Average KAST %"),
        ("Avg ADR", "Std ADR", "2. Firepower Output: Average Damage per Round (ADR)"),
        ("Avg ADR Diff", "Std ADR Diff", "3. Net Round Impact: Average ADR Difference"),
        ("Avg Kills", "Std Kills", "4. Kill Execution: Average Kills per Match"),
        ("Avg Open Kills", "Std Open Kills", "5. Opening Duels: Average Open Kills"),
        ("Avg Deaths", "Std Deaths", "6. Survival Deficit: Average Deaths per Match (Lower is Better)"),
        ("K/D Ratio", None, "7. Combat Efficiency: Total Kill/Death Ratio"),
        ("Win Rate %", None, "8. Match Success: Win Rate %"),
        ("Round Win Rate %", None, "9. Map Control: Round Win Rate %"),
        ("Avg Damage", "Std Damage", "10. Raw Chunk Output: Average Total Damage Dealt"),
        ("Avg Assists", "Std Assists", "11. Team Playmaking: Average Assists per Match"),
        ("Avg Trade Kills", "Std Trade Kills", "12. Support Retaliation: Average Trade Kills"),
        ("Avg Rounds Won", "Std Rounds Won", "13. Round Capitalization: Average Rounds Won"),
        ("Avg Rounds Lost", "Std Rounds Lost", "14. Economy Drain: Average Rounds Lost per Match"),
        ("Avg Rating", "Std Rating", "15. Ultimate Weighted Performance: HLTV Rating 2.1")
    ]

    # Render layout inside cleanly split twin columns
    chart_cols = st.columns(2)
    
    for idx, (avg_col, std_col, chart_title) in enumerate(metrics_to_chart):
        # Invert color scale and sorting arrays dynamically for lower-is-better data points
        ascending_sort = True if "Deaths" in chart_title or "Rounds Lost" in chart_title else False
        sorted_chart_df = leaderboard.sort_values(by=avg_col, ascending=ascending_sort)
        
        plot_config = {
            "data_frame": sorted_chart_df,
            "x": 'Player',
            "y": avg_col,
            "text": avg_col,
            "color": avg_col,
            "color_continuous_scale": 'Viridis' if not ascending_sort else 'Plasma',
            "title": chart_title
        }
        
        if std_col:
            plot_config["error_y"] = std_col
            
        fig = px.bar(**plot_config)
        fig.update_traces(textposition='outside', texttemplate='%{text:.2s}')
        fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))
        
        # Deploy column splits
        chart_cols[idx % 2].plotly_chart(fig, use_container_width=True)