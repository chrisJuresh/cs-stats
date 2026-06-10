import os
import pandas as pd
import plotly.express as px
import streamlit as st

# Configure the web page
st.set_page_config(page_title="CS2 Team Analytics", layout="wide", page_icon="📊")

st.title("📊 CS2 Match Analytics Dashboard")
st.markdown("---")

# Check if the master data file exists
if not os.path.exists("master_stats.csv"):
    st.error("🔴 'master_stats.csv' not found! Make sure you run your processing script first to generate the data.")
else:
    # Load the data
    df = pd.read_csv("master_stats.csv")
    
    # Ensure standard numeric data types for calculations
    df['K'] = pd.to_numeric(df['K'], errors='coerce')
    df['D'] = pd.to_numeric(df['D'], errors='coerce')
    df['ADR'] = pd.to_numeric(df['ADR'], errors='coerce')
    df['HLTV Rating 2.1'] = pd.to_numeric(df['HLTV Rating 2.1'], errors='coerce')
    df['Damage'] = pd.to_numeric(df['Damage'], errors='coerce')

    # Sidebar Filter
    st.sidebar.header("Navigation")
    view_mode = st.sidebar.radio("Go to:", ["Team Leaderboard", "Individual Player Stats"])

    # ----------------------------------------------------
    # VIEW 1: TEAM LEADERBOARD
    # ----------------------------------------------------
    if view_mode == "Team Leaderboard":
        st.header("🏆 Overall Player Leaderboard (Per-Match Averages & Consistency)")
        
        # Calculate lifetime averages AND standard deviations (for the error bars)
        leaderboard = df.groupby('Player').agg({
            'HLTV Rating 2.1': ['mean', 'std'],
            'ADR': ['mean', 'std'],
            'K': ['mean', 'std', 'sum'],
            'D': ['mean', 'std', 'sum'],
            'Damage': ['mean', 'std'],
            'Match ID': 'count'
        }).reset_index()
        
        # Flatten the multi-level columns created by agg()
        leaderboard.columns = [
            'Player', 
            'Avg Rating', 'Std Rating', 
            'Avg ADR', 'Std ADR', 
            'Avg Kills', 'Std Kills', 'Sum Kills', 
            'Avg Deaths', 'Std Deaths', 'Sum Deaths', 
            'Avg Damage', 'Std Damage', 
            'Matches Played'
        ]
        
        # Calculate accurate lifetime K/D ratio
        leaderboard['K/D Ratio'] = (leaderboard['Sum Kills'] / leaderboard['Sum Deaths']).round(2)
        
        # Round the averages for clean reading in the table
        leaderboard['Avg Rating'] = leaderboard['Avg Rating'].round(2)
        leaderboard['Avg ADR'] = leaderboard['Avg ADR'].round(1)
        leaderboard['Avg Kills'] = leaderboard['Avg Kills'].round(1)
        leaderboard['Avg Deaths'] = leaderboard['Avg Deaths'].round(1)
        leaderboard['Avg Damage'] = leaderboard['Avg Damage'].round(0)
        
        # Sort by best rating by default
        leaderboard = leaderboard.sort_values(by='Avg Rating', ascending=False)
        
        # Display the data table (filtering out the raw sums and std devs to keep it clean)
        display_df = leaderboard[['Player', 'Matches Played', 'Avg Rating', 'K/D Ratio', 'Avg ADR', 'Avg Kills', 'Avg Deaths', 'Avg Damage']]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 📈 Consistency Charts")
        st.caption("*Error bars represent the standard deviation across all matches played. Players with only 1 match will not show error bars.*")
        
        # Define the metrics we want to chart
        metrics_to_chart = [
            ("Avg Rating", "Std Rating", "HLTV Rating 2.1"),
            ("Avg ADR", "Std ADR", "Average Damage per Round (ADR)"),
            ("Avg Kills", "Std Kills", "Average Kills"),
            ("Avg Deaths", "Std Deaths", "Average Deaths"),
            ("Avg Damage", "Std Damage", "Average Total Damage")
        ]
        
        # Create a 2-column layout so it doesn't take up 5 pages of scrolling
        cols = st.columns(2)
        
        for i, (avg_col, std_col, title) in enumerate(metrics_to_chart):
            # Sort locally for each chart so the best player for that specific stat is on the left
            chart_data = leaderboard.sort_values(by=avg_col, ascending=False)
            
            fig = px.bar(
                chart_data, 
                x='Player', 
                y=avg_col, 
                error_y=std_col, # Plotly cleanly ignores NaN values here for 1-match players
                text=avg_col,
                color=avg_col, 
                color_continuous_scale='Viridis',
                title=title
            )
            # Formatting
            fig.update_traces(textposition='outside', texttemplate='%{text:.2s}')
            fig.update_layout(margin=dict(t=50, b=0, l=0, r=0))
            
            # Place in alternating columns
            cols[i % 2].plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------------
    # VIEW 2: INDIVIDUAL PLAYER STATS
    # ----------------------------------------------------
    else:
        st.header("👤 Player Profile Analysis")
        
        # Dropdown to pick player
        player_list = sorted(df['Player'].unique())
        selected_player = st.selectbox("Select a player to view history:", player_list)
        
        # Filter data for just that player
        p_df = df[df['Player'] == selected_player].copy()
        
        # Create unique label for match order
        p_df['Match Label'] = p_df['Match Score'] + " (" + p_df['Match ID'].astype(str) + ")"
        
        # Performance Summary Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg HLTV Rating", round(p_df['HLTV Rating 2.1'].mean(), 2))
        col2.metric("Avg ADR", round(p_df['ADR'].mean(), 1))
        col3.metric("Avg Kills/Match", round(p_df['K'].mean(), 1))
        col4.metric("Lifetime K/D Ratio", round(p_df['K'].sum() / p_df['D'].sum(), 2))
        
        # Chart: HLTV Rating Over Time
        st.markdown(f"### 📈 HLTV Rating Trend for {selected_player}")
        fig_trend = px.line(
            p_df, 
            x='Match Label', 
            y='HLTV Rating 2.1', 
            markers=True,
            labels={'HLTV Rating 2.1': 'HLTV Rating', 'Match Label': 'Match (Score)'}
        )
        # Add a baseline reference line for an average performance (1.00 rating)
        fig_trend.add_hline(y=1.0, line_dash="dash", line_color="red", annotation_text="Average Baseline (1.0)")
        st.plotly_chart(fig_trend, use_container_width=True)
        
        # Raw Player Match History Table
        st.markdown("### 📋 Recent Match History")
        st.dataframe(
            p_df[['Match ID', 'Match Score', 'Team', 'K', 'D', 'A', 'ADR', 'HLTV Rating 2.1']], 
            use_container_width=True, 
            hide_index=True
        )