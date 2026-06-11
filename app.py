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
    Directly reads the score string from the team's perspective.
    Since the scores are flipped, the first number is ALWAYS this team's rounds.
    """
    rounds_won_list = []
    rounds_lost_list = []
    result_list = []
    
    for idx, row in df.iterrows():
        score_str = str(row['Match Score'])
        
        try:
            # Extract the numbers from the score (e.g., "13-7" -> [13, 7])
            scores = [int(x) for x in re.findall(r'\d+', score_str)]
            if len(scores) >= 2:
                team_rounds = scores[0]
                enemy_rounds = scores[1]
                
                rounds_won_list.append(team_rounds)
                rounds_lost_list.append(enemy_rounds)
                
                if team_rounds > enemy_rounds:
                    result_list.append('Win')
                elif team_rounds < enemy_rounds:
                    result_list.append('Loss')
                else:
                    result_list.append('Draw')
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

    # Calculate Total Rounds played inside each individual match row
    df['Match Rounds'] = df['Rounds Won'] + df['Rounds Lost']
    df['Match Rounds'] = df['Match Rounds'].replace(0, pd.NA)

    # Generate Per-Round Metrics for each match entry row
    df['Kills_per_round'] = df['K'] / df['Match Rounds']
    df['Deaths_per_round'] = df['D'] / df['Match Rounds']
    df['Assists_per_round'] = df['A'] / df['Match Rounds']
    df['Open_kills_per_round'] = df['Open kills'] / df['Match Rounds']
    df['Trade_kills_per_round'] = df['Trade kills'] / df['Match Rounds']

    # 1. DATA AGGREGATION
    base_metrics = df.groupby('Player').agg({
        'Match ID': 'count',
        'KAST, %': ['mean', 'std'],
        'ADR': ['mean', 'std'],
        'Kills_per_round': ['mean', 'std'],
        'Open_kills_per_round': ['mean', 'std'],
        'Deaths_per_round': ['mean', 'std'],
        'ADR Differ...': ['mean', 'std'],
        'Assists_per_round': ['mean', 'std'],
        'Trade_kills_per_round': ['mean', 'std'],
        'K': ['sum'],
        'D': ['sum'],
        'A': ['sum'],
        'Damage': ['sum'],
        'Open kills': ['sum'],
        'Trade kills': ['sum'],
        'Rounds Won': ['sum', 'mean'],
        'Rounds Lost': ['sum', 'mean'],
        'HLTV Rating 2.1': ['mean', 'std']
    })
    
    # Flatten multi-index columns cleanly
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
        'Kills_per_round_mean': 'Kills per Round',
        'Open_kills_per_round_mean': 'Open Kills per Round',
        'Deaths_per_round_mean': 'Deaths per Round',
        'ADR Differ..._mean': 'Avg ADR Diff',
        'Assists_per_round_mean': 'Assists per Round',
        'Trade_kills_per_round_mean': 'Trade Kills per Round',
        'K_sum': 'Total Kills',
        'D_sum': 'Total Deaths',
        'A_sum': 'Total Assists',
        'Damage_sum': 'Total Damage',
        'Open kills_sum': 'Total Open Kills',
        'Trade kills_sum': 'Total Trade Kills',
        'Rounds Won_mean': 'Avg Rounds Won/Match',
        'Rounds Lost_mean': 'Avg Rounds Lost/Match',
        'HLTV Rating 2.1_mean': 'Avg Rating',
        # Standard deviations mapped behind the scenes for error bars
        'KAST, %_std': 'Std KAST %',
        'ADR_std': 'Std ADR',
        'Kills_per_round_std': 'Std Kills per Round',
        'Open_kills_per_round_std': 'Std Open Kills per Round',
        'Deaths_per_round_std': 'Std Deaths per Round',
        'ADR Differ..._std': 'Std ADR Diff',
        'Assists_per_round_std': 'Std Assists per Round',
        'Trade_kills_per_round_std': 'Std Trade Kills per Round',
        'HLTV Rating 2.1_std': 'Std Rating'
    }
    
    leaderboard = leaderboard.rename(columns=final_column_mapping)

    # Set rounding rules: 2 decimals for per-round values, 1 decimal for percentages/averages
    precision_2_cols = ['Kills per Round', 'Open Kills per Round', 'Deaths per Round', 'Assists per Round', 'Trade Kills per Round', 'Avg Rating', 'K/D Ratio']
    for col in precision_2_cols:
        leaderboard[col] = leaderboard[col].round(2)
        
    precision_1_cols = ['Avg KAST %', 'Avg ADR', 'Avg ADR Diff', 'Round Win Rate %', 'Win Rate %', 'Avg Rounds Won/Match', 'Avg Rounds Lost/Match']
    for col in precision_1_cols:
        leaderboard[col] = leaderboard[col].round(1)

    # Sort master table precisely by your specified core performance weights
    leaderboard = leaderboard.sort_values(by=['Avg KAST %', 'Avg ADR', 'Kills per Round'], ascending=[False, False, False])

    # Calculate overall ranking based on average position across all metrics
    ranking_metrics = [
        "Avg KAST %", "Avg ADR", "Kills per Round", "Open Kills per Round",
        "Avg ADR Diff", "Assists per Round", "Trade Kills per Round", "K/D Ratio", "Avg Rating"
    ]
    lower_is_better = {"Deaths per Round"}

    ranks = pd.DataFrame()
    for metric in ranking_metrics:
        ascending = metric in lower_is_better
        ranks[f'{metric}_rank'] = leaderboard[metric].rank(ascending=ascending, method='min')

    leaderboard['Overall Rank'] = ranks.iloc[:, :].mean(axis=1).round(1)

    # Display Master Metrics Data Grid Matrix
    st.subheader("📋 Complete Master Analytics Grid")
    st.write("Scroll horizontally to examine all metrics simultaneously.")

    table_display_order = [
        'Player', 'Overall Rank', 'Matches Played', 'Games Won', 'Games Lost', 'Games Drawn', 'Win Rate %',
        'Total Rounds Played', 'Total Rounds Won', 'Total Rounds Lost', 'Round Win Rate %',
        'Avg KAST %', 'Avg ADR', 'Avg ADR Diff',
        'Kills per Round', 'Total Kills',
        'Open Kills per Round', 'Total Open Kills',
        'Deaths per Round', 'Total Deaths',
        'Assists per Round', 'Total Assists', 'Total Damage',
        'Trade Kills per Round', 'Total Trade Kills', 'Avg Rounds Won/Match', 'Avg Rounds Lost/Match',
        'K/D Ratio', 'Avg Rating'
    ]
    st.dataframe(leaderboard[table_display_order], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("📈 All Performance Charts (In Core Order of Importance)")
    st.caption("*Error bars display standard deviation (consistency metric). Single match entries show no error bars.*")

    # Metrics sequence sorted perfectly per your layout logic guidelines
    metrics_to_chart = [
        ("Avg KAST %", "Std KAST %", "1. Round Contribution: Average KAST %"),
        ("Avg ADR", "Std ADR", "2. Firepower Output: Average Damage per Round (ADR)"),
        ("Kills per Round", "Std Kills per Round", "3. Frag Execution: Kills per Round"),
        ("Round Win Rate %", None, "11. Rounds Won: Round Win Rate %"),
        ("Win Rate %", None, "10. Match Success: Win Rate %"),
        ("Open Kills per Round", "Std Open Kills per Round", "4. Opening Duels: Open Kills per Round"),
        ("Deaths per Round", "Std Deaths per Round", "5. Survival Deficit: Deaths per Round (Lower is Better)"),
        ("Avg ADR Diff", "Std ADR Diff", "6. Net Impact: Average ADR Difference"),
        ("Assists per Round", "Std Assists per Round", "7. Team Playmaking: Assists per Round"),
        ("Trade Kills per Round", "Std Trade Kills per Round", "8. Support Retaliation: Trade Kills per Round"),
        ("K/D Ratio", None, "9. Kill/Death Efficiency Ratio"),
        ("Total Damage", None, "12. Aggregate Chunk Output: Total Lifetime Damage Dealt"),
        ("Total Kills", None, "13. Aggregate Frags: Total Lifetime Kills"),
        ("Total Deaths", None, "14. Aggregate Losses: Total Lifetime Deaths (Lower is Better)"),
        ("Avg Rating", "Std Rating", "15. Ultimate Weighted Performance: HLTV Rating 2.1"),
        ("Matches Played", None, "16. Matches Played: Total Games Per Player"),
        ("Overall Rank", None, "17. 🏆 Overall Ranking: Average Position Across All Metrics")
    ]

    # Render layout inside columns
    chart_cols = st.columns(2)

    for idx, (avg_col, std_col, chart_title) in enumerate(metrics_to_chart):
        if avg_col == "Matches Played":
            sorted_chart_df = leaderboard.sort_values(by=['Matches Played', 'Player'], ascending=[False, False])
        elif avg_col == "Overall Rank":
            ascending_sort = True
            color_scale = 'Viridis'
            sorted_chart_df = leaderboard.sort_values(by=avg_col, ascending=ascending_sort)
        else:
            ascending_sort = True if "Deaths" in chart_title or "Rounds Lost" in chart_title else False
            color_scale = 'Plasma' if ascending_sort else 'Viridis'
            sorted_chart_df = leaderboard.sort_values(by=avg_col, ascending=ascending_sort)

        if avg_col == "Matches Played":
            color_scale = 'Viridis'
        plot_config = {
            "data_frame": sorted_chart_df,
            "x": 'Player',
            "y": avg_col,
            "text": avg_col,
            "color": avg_col,
            "color_continuous_scale": color_scale,
            "title": chart_title
        }

        if std_col:
            plot_config["error_y"] = std_col

        fig = px.bar(**plot_config)

        # FIXING PLOTLY SI LABELS SYSTEM FORMATTING BUG
        # Assign custom numeric formatting maps based on column categories
        if avg_col == "Overall Rank" or avg_col in precision_2_cols:
            text_template = '%{text:.1f}'
            fig.update_layout(yaxis=dict(tickformat='.1f'))
        elif avg_col in ['Total Damage', 'Total Kills', 'Total Deaths', 'Total Rounds Played', 'Total Rounds Won', 'Total Rounds Lost', 'Matches Played']:
            text_template = '%{text:,}'
            fig.update_layout(yaxis=dict(tickformat=','))
        else:
            text_template = '%{text:.1f}'
            fig.update_layout(yaxis=dict(tickformat='.1f'))

        fig.update_traces(textposition='outside', texttemplate=text_template)
        fig.update_layout(margin=dict(t=50, b=10, l=10, r=10))

        # Deploy column splits
        chart_cols[idx % 2].plotly_chart(fig, use_container_width=True)