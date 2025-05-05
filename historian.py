import glob
import json
import os
import re
from collections import Counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pydantic import ValidationError

from src.models.simulation import SimulationState, Good

st.set_page_config(
    page_title="Mars Settlement Dashboard",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS to improve appearance
st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #ff6347;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
    }
    .metric-card {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card h3 {
        margin-top: 0;
    }
    .stDataFrame {
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stExpander {
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# Title with Mars icon
st.title("🔴 Mars Settlement Dashboard")
st.markdown("### Monitoring society's evolution from survival to flourishing")

# Setup sidebar for file selection and options
with st.sidebar:
    st.header("Data Controls")
    data_dir = st.text_input("Data Directory", "output")
    refresh_data = st.button("Refresh Data")
    st.divider()
    
    st.subheader("Visualizations")
    show_agent_details = st.checkbox("Show Agent Details", True)
    show_economy = st.checkbox("Show Economy", True)
    show_culture = st.checkbox("Show Culture", True)
    show_society = st.checkbox("Show Society Evolution", True)
    show_night = st.checkbox("Show Night Activities", True)
    
    st.divider()
    st.subheader("Data Export")
    
    # Export button functionality will be added in the main function
    
    st.divider()
    st.markdown("**Made for 2993 Mars Settlement Agency**")
    st.markdown("*Visualizing the evolution of Mars civilization*")


# Data Loading Function
@st.cache_data
def load_settlement_data(data_directory):
    """Load all state files and history from the given directory"""
    all_data = {}
    
    # Check if directory exists
    if not os.path.exists(data_directory):
        st.error(f"Directory '{data_directory}' not found.")
        return all_data
    
    # Find all day_*_state.json files
    state_files = glob.glob(os.path.join(data_directory, "day_*_state.json"))
    
    if not state_files:
        st.warning(f"No simulation state files found in '{data_directory}'. Expected files like 'day_1_state.json'")
        return all_data
    
    # Show progress bar for loading files
    progress_bar = st.progress(0)
    
    for i, file_path in enumerate(state_files):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Extract day number from filename
                day_match = re.search(r'day_(\d+)_state', file_path)
                if day_match:
                    day_num = int(day_match.group(1))
                    all_data[day_num] = data
                else:
                    st.warning(f"Couldn't extract day number from filename: {file_path}")
        except json.JSONDecodeError as e:
            st.error(f"JSON decode error in {file_path}: {str(e)}")
        except Exception as e:
            st.error(f"Error loading {file_path}: {str(e)}")
        
        # Update progress
        progress_bar.progress((i + 1) / len(state_files))
    
    # Also check for history.json if it exists
    history_path = os.path.join(data_directory, "history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                history_data = json.load(f)
                all_data['history'] = history_data
        except json.JSONDecodeError as e:
            st.error(f"JSON decode error in history.json: {str(e)}")
        except Exception as e:
            st.error(f"Error loading history.json: {str(e)}")
    
    # Clear progress bar when done
    progress_bar.empty()
    
    # Show summary of loaded data
    st.info(f"Loaded data for {len([k for k in all_data.keys() if isinstance(k, int)])} simulation days.")
    
    return all_data


# Process data into DataFrames for visualization
def process_settlement_data(data):
    """Transform the raw data into DataFrames for visualizations"""
    processed = {}

    # Extract days
    days = [d for d in data.keys() if isinstance(d, int)]
    days.sort()
    processed['days'] = days

    # Create agent DataFrame with daily snapshots
    agent_data = []
    ideas_data = []
    songs_data = []
    inventions_data = []
    market_data = []

    for day in days:
        try:
            # Try to validate the SimulationState data
            day_data = SimulationState.model_validate(data[day])
        except ValidationError as exc:
            st.warning(f"Error validating data for day {day}: {exc}")
            continue

        # Process agents
        for agent in day_data.agents:
            try:
                agent_id = agent.id
                agent_name = agent.name
                
                # Make sure goods are properly converted to Good objects
                if isinstance(agent.goods, list):
                    agent.goods = [Good.model_validate(g) if isinstance(g, dict) else g for g in agent.goods]
                
                # Basic agent properties
                agent_row = {
                    'day': day,
                    'agent_id': agent_id,
                    'agent_name': agent_name,
                    'age_days': agent.age_days,
                    'is_alive': agent.is_alive,
                    'credits': agent.credits,
                }

                # Add needs
                if hasattr(agent, 'needs') and agent.needs:
                    for need_type, value in agent.needs.items():
                        agent_row[f'need_{need_type}'] = value

                # Add goods count by type
                goods = agent.goods
                goods_by_type = Counter(good.type for good in goods)
                for good_type, count in goods_by_type.items():
                    agent_row[f'goods_{good_type}_count'] = count

                # Average goods quality by type
                for good_type in set(good.type for good in goods):
                    qualities = [good.quality for good in goods if good.type == good_type]
                    if qualities:
                        agent_row[f'goods_{good_type}_avg_quality'] = sum(qualities) / len(qualities)

                # Last action
                if hasattr(agent, 'history') and agent.history:
                    latest_action = agent.history[-1]
                    if isinstance(latest_action, tuple) and len(latest_action) >= 4:
                        action_data = latest_action[3]
                        if isinstance(action_data, dict):
                            agent_row['latest_action'] = action_data.get('type')

                            # Extract thoughts if available
                            if 'extras' in action_data and 'thoughts' in action_data['extras']:
                                thoughts = action_data['extras']['thoughts']
                                if isinstance(thoughts, str) and thoughts.strip():
                                    agent_row['latest_thoughts'] = thoughts

                agent_data.append(agent_row)
            except Exception as e:
                st.warning(f"Error processing agent {agent.id if hasattr(agent, 'id') else 'unknown'} on day {day}: {str(e)}")

        # Process market listings
        try:
            for listing in day_data.market.listings:
                market_row = {
                    'day': day,
                    'listing_id': listing.id,
                    'seller_id': listing.seller_id,
                    'price': listing.price,
                    'listed_on_day': listing.listed_on_day,
                }

                # Handle good data properly
                if hasattr(listing, 'good'):
                    good = listing.good
                    market_row['good_type'] = getattr(good, 'type', 'UNKNOWN')
                    market_row['good_name'] = getattr(good, 'name', 'Unknown Item')
                    market_row['good_quality'] = getattr(good, 'quality', 0)

                market_data.append(market_row)
        except Exception as e:
            st.warning(f"Error processing market data for day {day}: {str(e)}")

        # Process ideas
        try:
            # Handle ideas for this day
            day_ideas = day_data.ideas.get(day, [])
            for idea in day_ideas:
                if isinstance(idea, tuple) and len(idea) >= 2:
                    agent, thought = idea
                    
                    # Check if agent is an object with id and name attributes
                    if hasattr(agent, 'id') and hasattr(agent, 'name'):
                        idea_row = {
                            'day': day,
                            'agent_id': agent.id,
                            'agent_name': agent.name,
                            'idea_text': thought,
                        }
                        ideas_data.append(idea_row)
        except Exception as e:
            st.warning(f"Error processing ideas for day {day}: {str(e)}")

        # Process songs
        try:
            day_songs = day_data.songs
            if hasattr(day_songs, 'history_data') and day_songs.history_data:
                for song_day, songs_list in day_songs.history_data.items():
                    for entry in songs_list:
                        if hasattr(entry, 'agent') and hasattr(entry, 'song'):
                            song_row = {
                                'day': song_day,
                                'genre': entry.song.genre,
                                'title': entry.song.title,
                                'composer_id': entry.agent.id,
                                'composer_name': entry.agent.name,
                                'bpm': entry.song.bpm,
                            }
                            songs_data.append(song_row)
        except Exception as e:
            st.warning(f"Error processing songs for day {day}: {str(e)}")

        # Process inventions
        try:
            # Get inventions for this day
            day_inventions = day_data.inventions.get(day, [])
            for invention in day_inventions:
                if isinstance(invention, tuple) and len(invention) >= 2:
                    inventor, good = invention
                    
                    # Check if inventor is an object with id and name attributes
                    if hasattr(inventor, 'id') and hasattr(inventor, 'name'):
                        invention_row = {
                            'day': day,
                            'inventor_id': inventor.id,
                            'inventor_name': inventor.name,
                            'invention_type': getattr(good, 'type', 'UNKNOWN'),
                            'invention_name': getattr(good, 'name', 'Unknown Item'),
                            'invention_quality': getattr(good, 'quality', 0),
                        }
                        inventions_data.append(invention_row)
        except Exception as e:
            st.warning(f"Error processing inventions for day {day}: {str(e)}")

    # Convert to DataFrames
    processed['agents_df'] = pd.DataFrame(agent_data)
    processed['market_df'] = pd.DataFrame(market_data)
    processed['ideas_df'] = pd.DataFrame(ideas_data)
    processed['songs_df'] = pd.DataFrame(songs_data)
    processed['inventions_df'] = pd.DataFrame(inventions_data)

    # Create action counts by day
    if not processed['agents_df'].empty and 'latest_action' in processed['agents_df'].columns:
        action_counts = processed['agents_df'].groupby(['day', 'latest_action']).size().reset_index(name='count')
        processed['action_counts_df'] = action_counts

    # Process night activities data
    night_activities_data = []
    
    for day in days:
        try:
            day_data = SimulationState.model_validate(data[day])
            
            # Process night activities
            today_activities = day_data.night_activities.get(day, [])
            for activity in today_activities:
                if hasattr(activity, 'agent_id'):
                    # Basic activity data
                    activity_row = {
                        'day': day,
                        'agent_id': activity.agent_id,
                    }
                    
                    # Get agent name
                    agent = day_data.get_agent_by_id(activity.agent_id)
                    if agent:
                        activity_row['agent_name'] = agent.name
                    else:
                        activity_row['agent_name'] = "Unknown"
                    
                    # Add song choice if present
                    if hasattr(activity, 'song_choice_title') and activity.song_choice_title:
                        activity_row['song_choice'] = activity.song_choice_title
                    
                    # Add letter data if present
                    if hasattr(activity, 'letters') and activity.letters:
                        activity_row['sent_letters'] = len(activity.letters)
                        if len(activity.letters) > 0:
                            # Store the first letter's recipient and title for display
                            activity_row['letter_recipient'] = activity.letters[0].recipient_name
                            activity_row['letter_title'] = activity.letters[0].title
                    
                    # Add dinner data if present
                    if hasattr(activity, 'dinner_consumed') and activity.dinner_consumed:
                        activity_row['dinner_items'] = len(activity.dinner_consumed)
                        if activity.dinner_consumed:
                            # Calculate average quality of dinner
                            qualities = [item.quality for item in activity.dinner_consumed if hasattr(item, 'quality')]
                            if qualities:
                                activity_row['avg_dinner_quality'] = sum(qualities) / len(qualities)
                    
                    night_activities_data.append(activity_row)
        except Exception as e:
            st.warning(f"Error processing night activities for day {day}: {str(e)}")
    
    # Add the night activities dataframe to processed data
    processed['night_activities_df'] = pd.DataFrame(night_activities_data)

    return processed


# Create the main dashboard
def create_dashboard(processed_data):
    """Create the main dashboard with tabs for different aspects"""
    # Create a list of tab names based on sidebar settings
    tab_names = ["Overview"]
    
    if show_agent_details:
        tab_names.append("Agents")
    
    if show_economy:
        tab_names.append("Economy")
    
    if show_culture:
        tab_names.append("Culture")
    
    if show_night:
        tab_names.append("Night Activities")
    
    if show_society:
        tab_names.append("Society Evolution")
    
    # Always include Timeline
    tab_names.append("Timeline")
    
    # Create tabs based on visible options
    tabs = st.tabs(tab_names)

    # Get DataFrames
    agents_df = processed_data.get('agents_df', pd.DataFrame())
    market_df = processed_data.get('market_df', pd.DataFrame())
    ideas_df = processed_data.get('ideas_df', pd.DataFrame())
    songs_df = processed_data.get('songs_df', pd.DataFrame())
    inventions_df = processed_data.get('inventions_df', pd.DataFrame())
    action_counts_df = processed_data.get('action_counts_df', pd.DataFrame())
    night_activities_df = processed_data.get('night_activities_df', pd.DataFrame())
    days = processed_data.get('days', [])

    # Track the current tab index
    tab_idx = 0

    # Overview Tab
    with tabs[tab_idx]:
        st.header("Mars Settlement Overview")

        col1, col2, col3 = st.columns(3)

        # Key metrics
        with col1:
            if not agents_df.empty:
                st.metric("Total Population", len(agents_df['agent_id'].unique()))
                avg_credits = agents_df.groupby('day')['credits'].mean().iloc[-1] if not agents_df.empty else 0
                st.metric("Average Credits", f"{avg_credits:.2f}")

        with col2:
            if not inventions_df.empty:
                st.metric("Total Inventions", len(inventions_df))
            if not ideas_df.empty:
                st.metric("Total Ideas", len(ideas_df))

        with col3:
            if not agents_df.empty:
                latest_day = max(agents_df['day']) if not agents_df.empty else 0
                st.metric("Current Day", latest_day)
            if not songs_df.empty:
                st.metric("Total Songs", len(songs_df))

        # Actions summary chart
        if not action_counts_df.empty:
            st.subheader("Settlement Activities")

            fig = px.bar(
                action_counts_df,
                x='day',
                y='count',
                color='latest_action',
                title='Agent Actions by Day',
                barmode='stack'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # Recent events
        st.subheader("Recent Events")

        col1, col2 = st.columns(2)

        # Recent ideas
        with col1:
            st.markdown("**Latest Ideas**")
            if not ideas_df.empty:
                latest_ideas = ideas_df.sort_values('day', ascending=False).head(3)
                for _, idea in latest_ideas.iterrows():
                    with st.expander(f"Day {idea['day']} - {idea['agent_name']}"):
                        st.write(idea['idea_text'])
            else:
                st.write("No ideas recorded yet.")

        # Recent inventions
        with col2:
            st.markdown("**Latest Inventions**")
            if not inventions_df.empty:
                latest_inventions = inventions_df.sort_values('day', ascending=False).head(3)
                for _, invention in latest_inventions.iterrows():
                    st.write(
                        f"Day {invention['day']}: {invention['inventor_name']} created '{invention['invention_name']}' (Quality: {invention['invention_quality']:.2f})")
            else:
                st.write("No inventions recorded yet.")

    tab_idx += 1
    
    # Agents Tab (only if enabled)
    if show_agent_details:
        with tabs[tab_idx]:
            st.header("Agent Analytics")

            # Agent selector
            agent_ids = sorted(agents_df['agent_id'].unique()) if not agents_df.empty else []
            
            if agent_ids:
                # Helper function to get agent name
                def get_agent_name(agent_id):
                    agent_data = agents_df[agents_df['agent_id'] == agent_id]
                    return agent_data['agent_name'].iloc[0] if not agent_data.empty else agent_id
                
                selected_agent = st.selectbox("Select Agent", agent_ids, format_func=get_agent_name)
                
                if selected_agent:
                    agent_data = agents_df[agents_df['agent_id'] == selected_agent]
                    
                    # Agent profile
                    st.subheader(agent_data['agent_name'].iloc[0])

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Age (Days)", agent_data['age_days'].iloc[0])
                    with col2:
                        st.metric("Credits", f"{agent_data['credits'].iloc[-1]:.2f}")
                    with col3:
                        st.metric("Status", "Alive" if agent_data['is_alive'].iloc[0] else "Deceased")

                    # Needs over time chart
                    st.subheader("Needs Over Time")

                    # Get needs columns
                    needs_columns = [col for col in agent_data.columns if col.startswith('need_')]

                    if needs_columns:
                        # Prepare data for plotting
                        needs_data = agent_data[['day'] + needs_columns].melt(
                            id_vars=['day'],
                            value_vars=needs_columns,
                            var_name='need_type',
                            value_name='value'
                        )
                        # Clean up need type names
                        needs_data['need_type'] = needs_data['need_type'].str.replace('need_', '')

                        # Create line chart
                        fig = px.line(
                            needs_data,
                            x='day',
                            y='value',
                            color='need_type',
                            title='Agent Needs Over Time',
                            labels={'value': 'Need Level', 'need_type': 'Need Type'},
                            color_discrete_map={'food': 'green', 'rest': 'blue', 'fun': 'orange'}
                        )
                        fig.update_layout(yaxis_range=[0, 1], height=400)
                        st.plotly_chart(fig, use_container_width=True)

                    # Actions breakdown
                    if 'latest_action' in agent_data.columns:
                        st.subheader("Actions Taken")
                        action_counts = agent_data['latest_action'].value_counts().reset_index()
                        action_counts.columns = ['Action', 'Count']

                        fig = px.pie(
                            action_counts,
                            values='Count',
                            names='Action',
                            title='Agent Actions Breakdown'
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

                    # Agent goods over time
                    goods_columns = [col for col in agent_data.columns if col.startswith('goods_') and 'count' in col]
                    if goods_columns:
                        st.subheader("Goods Possessed Over Time")

                        # Prepare data for plotting
                        goods_data = agent_data[['day'] + goods_columns].melt(
                            id_vars=['day'],
                            value_vars=goods_columns,
                            var_name='good_type',
                            value_name='count'
                        )
                        # Clean up good type names
                        goods_data['good_type'] = goods_data['good_type'].str.replace('goods_', '').str.replace('_count',
                                                                                                                '')

                        # Create line chart
                        fig = px.line(
                            goods_data,
                            x='day',
                            y='count',
                            color='good_type',
                            title='Agent Goods Over Time',
                            labels={'count': 'Count', 'good_type': 'Good Type'}
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)

                    # Latest thoughts
                    if 'latest_thoughts' in agent_data.columns:
                        thoughts = agent_data.sort_values('day', ascending=False)['latest_thoughts'].iloc[0]
                        if pd.notna(thoughts):
                            st.subheader("Latest Thoughts")
                            st.write(thoughts)

                    # After the agent's day actions section, add night activities
                    if not night_activities_df.empty and 'agent_id' in night_activities_df.columns:
                        agent_night_activities = night_activities_df[night_activities_df['agent_id'] == selected_agent]
                        
                        if not agent_night_activities.empty:
                            st.subheader("Night Activities")
                            
                            # Display a table of night activities
                            st.markdown("**Evening activities and social interactions**")
                            
                            # Create a more readable display table
                            display_data = []
                            for _, activity in agent_night_activities.iterrows():
                                row = {
                                    'Day': activity['day'],
                                    'Activities': []
                                }
                                
                                if 'song_choice' in activity and pd.notna(activity['song_choice']):
                                    row['Activities'].append(f"Listened to '{activity['song_choice']}'")
                                
                                if 'sent_letters' in activity and activity['sent_letters'] > 0:
                                    recipient_info = f" to {activity['letter_recipient']}" if 'letter_recipient' in activity and pd.notna(activity['letter_recipient']) else ""
                                    row['Activities'].append(f"Sent letter{recipient_info}")
                                
                                if 'dinner_items' in activity and activity['dinner_items'] > 0:
                                    dinner_quality = f" (Quality: {activity['avg_dinner_quality']:.2f})" if 'avg_dinner_quality' in activity and pd.notna(activity['avg_dinner_quality']) else ""
                                    row['Activities'].append(f"Had dinner{dinner_quality}")
                                
                                # Join all activities for display
                                row['Activity Summary'] = ", ".join(row['Activities']) if row['Activities'] else "No recorded activities"
                                del row['Activities']  # Remove the list before displaying
                                
                                display_data.append(row)
                            
                            # Display as a dataframe
                            if display_data:
                                display_df = pd.DataFrame(display_data)
                                st.dataframe(display_df)
                            else:
                                st.info("No night activities recorded for this agent.")
                else:
                    st.write("No agent selected.")
            else:
                st.write("No agent data available.")
                
        tab_idx += 1
    
    # Economy Tab (only if enabled)
    if show_economy:
        with tabs[tab_idx]:
            st.header("Economic Analytics")

            # Market activity
            if not market_df.empty:
                st.subheader("Market Activity")

                # Listings over time
                listings_by_day = market_df.groupby('day').size().reset_index(name='count')

                fig = px.line(
                    listings_by_day,
                    x='day',
                    y='count',
                    title='Market Listings Over Time',
                    labels={'count': 'Number of Listings', 'day': 'Day'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                # Price trends by good type
                if 'good_type' in market_df.columns:
                    st.subheader("Price Trends by Good Type")

                    avg_prices = market_df.groupby(['day', 'good_type'])['price'].mean().reset_index()

                    fig = px.line(
                        avg_prices,
                        x='day',
                        y='price',
                        color='good_type',
                        title='Average Market Prices by Good Type',
                        labels={'price': 'Average Price', 'day': 'Day', 'good_type': 'Good Type'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                # Quality vs. Price scatter plot
                if 'good_quality' in market_df.columns:
                    st.subheader("Item Quality vs. Price")

                    fig = px.scatter(
                        market_df,
                        x='good_quality',
                        y='price',
                        color='good_type',
                        hover_data=['good_name', 'day'],
                        title='Item Quality vs. Price',
                        labels={'good_quality': 'Item Quality', 'price': 'Price', 'good_type': 'Good Type'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

            # Agent wealth distribution
            if not agents_df.empty:
                st.subheader("Agent Wealth Distribution")

                latest_day = max(agents_df['day'])
                latest_agents = agents_df[agents_df['day'] == latest_day]

                fig = px.histogram(
                    latest_agents,
                    x='credits',
                    nbins=20,
                    title=f'Agent Wealth Distribution (Day {latest_day})',
                    labels={'credits': 'Credits', 'count': 'Number of Agents'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                # Wealth inequality chart (if we have enough data)
                if len(latest_agents) > 5:
                    st.subheader("Wealth Inequality")

                    # Sort agents by credits
                    sorted_agents = latest_agents.sort_values('credits')
                    # Calculate cumulative percentage of total wealth
                    total_wealth = sorted_agents['credits'].sum()
                    sorted_agents['wealth_percentile'] = sorted_agents['credits'].cumsum() / total_wealth * 100
                    sorted_agents['population_percentile'] = np.linspace(0, 100, len(sorted_agents))

                    fig = px.line(
                        sorted_agents,
                        x='population_percentile',
                        y='wealth_percentile',
                        title='Lorenz Curve of Wealth Distribution',
                        labels={
                            'population_percentile': 'Cumulative % of Population',
                            'wealth_percentile': 'Cumulative % of Wealth'
                        }
                    )

                    # Add perfect equality line
                    fig.add_trace(
                        go.Scatter(
                            x=[0, 100],
                            y=[0, 100],
                            mode='lines',
                            name='Perfect Equality',
                            line=dict(dash='dash', color='gray')
                        )
                    )

                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No economic data available.")
        tab_idx += 1
    
    # Culture Tab (only if enabled)
    if show_culture:
        with tabs[tab_idx]:
            st.header("Cultural Analytics")

            col1, col2 = st.columns(2)

            # Inventions analysis
            with col1:
                st.subheader("Inventions")

                if not inventions_df.empty:
                    # Inventions over time
                    inventions_by_day = inventions_df.groupby('day').size().reset_index(name='count')
                    inventions_by_day = inventions_by_day.set_index('day').reindex(days, fill_value=0).reset_index()

                    fig = px.bar(
                        inventions_by_day,
                        x='day',
                        y='count',
                        title='Inventions Over Time',
                        labels={'count': 'Number of Inventions', 'day': 'Day'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

                    # Invention quality distribution
                    fig = px.histogram(
                        inventions_df,
                        x='invention_quality',
                        nbins=20,
                        title='Invention Quality Distribution',
                        labels={'invention_quality': 'Quality', 'count': 'Number of Inventions'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

                    # Top inventors
                    st.subheader("Top Inventors")
                    inventor_counts = inventions_df['inventor_name'].value_counts().reset_index()
                    inventor_counts.columns = ['Inventor', 'Inventions']
                    st.dataframe(inventor_counts.head(5))
                else:
                    st.write("No invention data available yet.")

            # Ideas analysis
            with col2:
                st.subheader("Ideas")

                if not ideas_df.empty:
                    # Ideas over time
                    ideas_by_day = ideas_df.groupby('day').size().reset_index(name='count')
                    ideas_by_day = ideas_by_day.set_index('day').reindex(days, fill_value=0).reset_index()

                    fig = px.bar(
                        ideas_by_day,
                        x='day',
                        y='count',
                        title='Ideas Over Time',
                        labels={'count': 'Number of Ideas', 'day': 'Day'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

                    # Top idea generators
                    idea_counts = ideas_df['agent_name'].value_counts().reset_index()
                    idea_counts.columns = ['Agent', 'Ideas']

                    fig = px.bar(
                        idea_counts.head(5),
                        x='Agent',
                        y='Ideas',
                        title='Top Idea Generators',
                        labels={'Ideas': 'Number of Ideas', 'Agent': 'Agent Name'}
                    )
                    fig.update_layout(height=300)
                    st.plotly_chart(fig, use_container_width=True)

                    # Word cloud of ideas (if wordcloud library is available)
                    try:
                        from wordcloud import WordCloud

                        st.subheader("Ideas Word Cloud")

                        # Combine all ideas into one text
                        all_ideas = ' '.join(ideas_df['idea_text'].dropna())

                        if all_ideas:
                            # Generate word cloud
                            wordcloud = WordCloud(
                                width=800,
                                height=400,
                                background_color='white',
                                max_words=100
                            ).generate(all_ideas)

                            # Display the word cloud
                            plt.figure(figsize=(10, 5))
                            plt.imshow(wordcloud, interpolation='bilinear')
                            plt.axis('off')
                            st.pyplot(plt)
                    except ImportError:
                        st.info("Install 'wordcloud' library to see ideas word cloud visualization.")
                else:
                    st.write("No idea data available yet.")

            # Songs analysis
            if not songs_df.empty:
                st.subheader("Music & Songs")

                # Songs by genre
                genre_counts = songs_df['genre'].value_counts().reset_index()
                genre_counts.columns = ['Genre', 'Count']

                fig = px.pie(
                    genre_counts,
                    values='Count',
                    names='Genre',
                    title='Songs by Genre'
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                # Top composers
                composer_counts = songs_df['composer_name'].value_counts().reset_index()
                composer_counts.columns = ['Composer', 'Songs']

                fig = px.bar(
                    composer_counts.head(5),
                    x='Composer',
                    y='Songs',
                    title='Top Composers',
                    labels={'Songs': 'Number of Songs', 'Composer': 'Composer Name'}
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

                # Recent songs
                st.subheader("Recent Songs")
                recent_songs = songs_df.sort_values('day', ascending=False).head(5)
                for _, song in recent_songs.iterrows():
                    st.write(
                        f"Day {song['day']}: '{song['title']}' by {song['composer_name']} ({song['genre']}, {song['bpm']} BPM)")
            else:
                st.write("No song data available yet.")
        tab_idx += 1
    
    # Night Activities Tab (only if enabled)
    if show_night:
        with tabs[tab_idx]:
            st.header("Night Activities Analysis")
            
            if not night_activities_df.empty:
                # Activity statistics
                st.subheader("Social Interactions")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Letters sent over time
                    if 'sent_letters' in night_activities_df.columns:
                        letters_by_day = night_activities_df.groupby('day')['sent_letters'].sum().reset_index()
                        
                        fig = px.line(
                            letters_by_day,
                            x='day',
                            y='sent_letters',
                            title='Letters Sent Over Time',
                            labels={'sent_letters': 'Number of Letters', 'day': 'Day'}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Top letter senders
                        if 'sent_letters' in night_activities_df.columns:
                            letter_senders = night_activities_df.groupby('agent_name')['sent_letters'].sum().reset_index()
                            letter_senders = letter_senders.sort_values('sent_letters', ascending=False).head(5)
                            
                            fig = px.bar(
                                letter_senders,
                                x='agent_name',
                                y='sent_letters',
                                title='Top Letter Senders',
                                labels={'sent_letters': 'Letters Sent', 'agent_name': 'Agent'}
                            )
                            fig.update_layout(height=300)
                            st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Song listening over time
                    if 'song_choice' in night_activities_df.columns:
                        songs_by_day = night_activities_df['song_choice'].notna().groupby(night_activities_df['day']).sum().reset_index()
                        songs_by_day.columns = ['day', 'songs_listened']
                        
                        fig = px.line(
                            songs_by_day,
                            x='day',
                            y='songs_listened',
                            title='Songs Listened Over Time',
                            labels={'songs_listened': 'Number of Songs', 'day': 'Day'}
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Dinner quality over time
                    if 'avg_dinner_quality' in night_activities_df.columns:
                        dinner_quality_by_day = night_activities_df.groupby('day')['avg_dinner_quality'].mean().reset_index()
                        
                        fig = px.line(
                            dinner_quality_by_day,
                            x='day',
                            y='avg_dinner_quality',
                            title='Average Dinner Quality Over Time',
                            labels={'avg_dinner_quality': 'Average Quality', 'day': 'Day'}
                        )
                        fig.update_layout(height=300, yaxis_range=[0, 1])
                        st.plotly_chart(fig, use_container_width=True)
                
                # Most popular songs
                if 'song_choice' in night_activities_df.columns:
                    st.subheader("Popular Music")
                    popular_songs = night_activities_df['song_choice'].value_counts().reset_index()
                    popular_songs.columns = ['Song', 'Times Listened']
                    popular_songs = popular_songs.head(10)
                    
                    if not popular_songs.empty and len(popular_songs) > 0:
                        fig = px.bar(
                            popular_songs,
                            x='Song',
                            y='Times Listened',
                            title='Most Popular Songs',
                            labels={'Times Listened': 'Plays', 'Song': 'Song Title'}
                        )
                        fig.update_layout(height=400)
                        st.plotly_chart(fig, use_container_width=True)
                
                # Recent night activities
                st.subheader("Recent Night Activities")
                recent = night_activities_df.sort_values('day', ascending=False).head(10)
                
                for _, activity in recent.iterrows():
                    activity_details = []
                    
                    # Add details based on what information is available
                    if 'song_choice' in activity and pd.notna(activity['song_choice']):
                        activity_details.append(f"Listened to '{activity['song_choice']}'")
                    
                    if 'sent_letters' in activity and activity['sent_letters'] > 0:
                        recipient_info = f" to {activity['letter_recipient']}" if 'letter_recipient' in activity and pd.notna(activity['letter_recipient']) else ""
                        letter_title = f" titled '{activity['letter_title']}'" if 'letter_title' in activity and pd.notna(activity['letter_title']) else ""
                        activity_details.append(f"Sent letter{recipient_info}{letter_title}")
                    
                    if 'dinner_items' in activity and activity['dinner_items'] > 0:
                        dinner_quality = f" (Quality: {activity['avg_dinner_quality']:.2f})" if 'avg_dinner_quality' in activity and pd.notna(activity['avg_dinner_quality']) else ""
                        activity_details.append(f"Had dinner with {activity['dinner_items']} items{dinner_quality}")
                    
                    # Format the output with expander for details
                    with st.expander(f"Day {activity['day']}: {activity['agent_name']}"):
                        if activity_details:
                            for detail in activity_details:
                                st.write(f"• {detail}")
                        else:
                            st.write("No detailed activities recorded")
            else:
                st.info("No night activities data available. Enable night activities in your simulation to see this data.")
    
    # Society Evolution Tab (now tab 5 instead of 4)
    with tabs[5]:
        if show_society:
            st.header("Society Evolution")

            # Track society's evolution from survival to flourishing
            if not agents_df.empty and len(days) > 1:
                # Calculate metrics over time
                society_metrics = []

                for day in days:
                    day_agents = agents_df[agents_df['day'] == day]

                    if day_agents.empty:
                        continue

                    # Calculate metrics
                    avg_food = day_agents['need_food'].mean() if 'need_food' in day_agents.columns else None
                    avg_rest = day_agents['need_rest'].mean() if 'need_rest' in day_agents.columns else None
                    avg_fun = day_agents['need_fun'].mean() if 'need_fun' in day_agents.columns else None

                    # Count actions if available
                    if 'latest_action' in day_agents.columns:
                        action_counts = day_agents['latest_action'].value_counts()
                        work_count = action_counts.get('WORK', 0)
                        rest_count = action_counts.get('REST', 0)
                        craft_count = action_counts.get('CRAFT', 0)
                        think_count = action_counts.get('THINK', 0)
                        compose_count = action_counts.get('COMPOSE', 0)
                    else:
                        work_count = rest_count = craft_count = think_count = compose_count = 0

                    # Get inventions count for this day
                    day_inventions = inventions_df[inventions_df['day'] == day].shape[
                        0] if not inventions_df.empty else 0
                    day_ideas = ideas_df[ideas_df['day'] == day].shape[0] if not ideas_df.empty else 0
                    day_songs = songs_df[songs_df['day'] == day].shape[0] if not songs_df.empty else 0

                    # Calculate survival vs. flourishing index
                    # Higher = more flourishing, lower = more survival-focused
                    survival_actions = work_count + rest_count
                    flourishing_actions = craft_count + think_count + compose_count

                    total_actions = survival_actions + flourishing_actions
                    if total_actions > 0:
                        flourishing_ratio = flourishing_actions / total_actions
                    else:
                        flourishing_ratio = 0

                    # Creative output
                    creative_output = day_inventions + day_ideas + day_songs

                    # Calculate avg goods quality
                    quality_cols = [col for col in day_agents.columns if 'avg_quality' in col]
                    if quality_cols:
                        avg_qualities = []
                        for col in quality_cols:
                            avg_qualities.extend(day_agents[col].dropna().tolist())

                        avg_quality = np.mean(avg_qualities) if avg_qualities else 0
                    else:
                        avg_quality = 0

                    # Combine into an overall society index
                    # This is a simplified model that could be refined
                    society_index = (
                            (avg_food if avg_food is not None else 0.5) * 0.2 +  # Basic needs
                            (avg_rest if avg_rest is not None else 0.5) * 0.2 +  # Basic needs
                            flourishing_ratio * 0.3 +  # Flourishing activities
                            min(creative_output / max(len(day_agents), 1), 1) * 0.2 +  # Creative output (capped)
                            avg_quality * 0.1  # Quality of goods
                    )

                    society_metrics.append({
                        'day': day,
                        'avg_food': avg_food,
                        'avg_rest': avg_rest,
                        'avg_fun': avg_fun,
                        'work_count': work_count,
                        'rest_count': rest_count,
                        'craft_count': craft_count,
                        'think_count': think_count,
                        'compose_count': compose_count,
                        'inventions': day_inventions,
                        'ideas': day_ideas,
                        'songs': day_songs,
                        'flourishing_ratio': flourishing_ratio,
                        'creative_output': creative_output,
                        'avg_quality': avg_quality,
                        'society_index': society_index
                    })

                # Convert to DataFrame
                society_df = pd.DataFrame(society_metrics)

                if not society_df.empty:
                    # Survival to Flourishing Index
                    st.subheader("Survival to Flourishing Index")
                    st.write(
                        "This index measures the settlement's progress from survival-focused activities to flourishing creativity.")

                    fig = px.line(
                        society_df,
                        x='day',
                        y='society_index',
                        title='Society Evolution Index',
                        labels={'society_index': 'Flourishing Index', 'day': 'Day'}
                    )

                    # Add horizontal threshold lines
                    fig.add_shape(
                        type="line", line=dict(dash='dash', color='red'),
                        x0=min(days), x1=max(days), y0=0.3, y1=0.3
                    )
                    fig.add_shape(
                        type="line", line=dict(dash='dash', color='orange'),
                        x0=min(days), x1=max(days), y0=0.5, y1=0.5
                    )
                    fig.add_shape(
                        type="line", line=dict(dash='dash', color='green'),
                        x0=min(days), x1=max(days), y0=0.7, y1=0.7
                    )

                    # Add annotations for the threshold lines
                    fig.add_annotation(
                        x=max(days), y=0.3, text="Survival", showarrow=False,
                        font=dict(color="red"), xanchor="right"
                    )
                    fig.add_annotation(
                        x=max(days), y=0.5, text="Stability", showarrow=False,
                        font=dict(color="orange"), xanchor="right"
                    )
                    fig.add_annotation(
                        x=max(days), y=0.7, text="Flourishing", showarrow=False,
                        font=dict(color="green"), xanchor="right"
                    )

                    fig.update_layout(height=400, yaxis_range=[0, 1])
                    st.plotly_chart(fig, use_container_width=True)

                    # Components breakdown
                    st.subheader("Evolution Components")

                    # Activity type breakdown
                    activity_data = society_df[
                        ['day', 'work_count', 'rest_count', 'craft_count', 'think_count', 'compose_count']]
                    activity_data = activity_data.melt(
                        id_vars=['day'],
                        value_vars=['work_count', 'rest_count', 'craft_count', 'think_count', 'compose_count'],
                        var_name='activity_type',
                        value_name='count'
                    )

                    # Clean up activity names
                    activity_data['activity_type'] = activity_data['activity_type'].str.replace('_count', '')

                    fig = px.area(
                        activity_data,
                        x='day',
                        y='count',
                        color='activity_type',
                        title='Activity Types Over Time',
                        labels={'count': 'Activity Count', 'day': 'Day', 'activity_type': 'Activity Type'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                    # Creative output over time
                    creative_data = society_df[['day', 'inventions', 'ideas', 'songs']]
                    creative_data = creative_data.melt(
                        id_vars=['day'],
                        value_vars=['inventions', 'ideas', 'songs'],
                        var_name='output_type',
                        value_name='count'
                    )

                    fig = px.area(
                        creative_data,
                        x='day',
                        y='count',
                        color='output_type',
                        title='Creative Output Over Time',
                        labels={'count': 'Output Count', 'day': 'Day', 'output_type': 'Output Type'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)

                    # Average needs satisfaction
                    needs_data = society_df[['day', 'avg_food', 'avg_rest', 'avg_fun']].dropna()
                    if not needs_data.empty:
                        needs_data = needs_data.melt(
                            id_vars=['day'],
                            value_vars=['avg_food', 'avg_rest', 'avg_fun'],
                            var_name='need_type',
                            value_name='satisfaction'
                        )

                        # Clean up need names
                        needs_data['need_type'] = needs_data['need_type'].str.replace('avg_', '')

                        fig = px.line(
                            needs_data,
                            x='day',
                            y='satisfaction',
                            color='need_type',
                            title='Average Needs Satisfaction',
                            labels={'satisfaction': 'Satisfaction Level', 'day': 'Day', 'need_type': 'Need Type'},
                            color_discrete_map={'food': 'green', 'rest': 'blue', 'fun': 'orange'}
                        )
                        fig.update_layout(height=400, yaxis_range=[0, 1])
                        st.plotly_chart(fig, use_container_width=True)

                # Society stage assessment
                current_index = society_df['society_index'].iloc[-1] if not society_df.empty else 0

                st.subheader("Current Society Stage Assessment")

                if current_index < 0.3:
                    stage = "Survival Stage"
                    description = """
                    The settlement is focused on basic survival needs. Most agents prioritize work, rest, and food gathering 
                    with little capacity for creative or cultural development. Resources are primarily allocated to essential needs.
                    """
                elif current_index < 0.5:
                    stage = "Stability Stage"
                    description = """
                    Basic survival needs are mostly met, allowing some agents to begin creative pursuits. 
                    The settlement has established basic systems for resource allocation, and occasional cultural 
                    activities are emerging. Crafting of better goods is becoming more common.
                    """
                elif current_index < 0.7:
                    stage = "Growth Stage"
                    description = """
                    The settlement has moved beyond mere survival and stability. A significant portion of agent activity 
                    is devoted to improvement and creation. Regular cultural activities, invention of higher quality goods, 
                    and creative thinking are common. The foundation for a flourishing society is being established.
                    """
                else:
                    stage = "Flourishing Stage"
                    description = """
                    The settlement has evolved into a creative, innovative society. Agents regularly engage in arts, 
                    creative thinking, and invention. High-quality goods are common, and a rich cultural ecosystem has 
                    developed. The settlement exemplifies a thriving Mars civilization.
                    """

                col1, col2 = st.columns([1, 3])

                with col1:
                    if current_index < 0.3:
                        st.image("https://via.placeholder.com/300/FF4500/FFFFFF?text=Survival", use_column_width=True)
                    elif current_index < 0.5:
                        st.image("https://via.placeholder.com/300/FFA500/FFFFFF?text=Stability", use_column_width=True)
                    elif current_index < 0.7:
                        st.image("https://via.placeholder.com/300/32CD32/FFFFFF?text=Growth", use_column_width=True)
                    else:
                        st.image("https://via.placeholder.com/300/1E90FF/FFFFFF?text=Flourishing",
                                 use_column_width=True)

                with col2:
                    st.markdown(f"### {stage}")
                    st.write(description)
                    st.metric("Society Index", f"{current_index:.2f}")
            else:
                st.write("Not enough data to analyze society evolution yet.")
        else:
            st.info("Enable 'Show Society Evolution' in the sidebar to view societal analytics.")

    # Timeline Tab (always included, so no if check needed)
    with tabs[tab_idx]:
        st.header("Simulation Timeline")
        
        if days:
            # Day selector
            min_day = min(days)
            max_day = max(days)
            selected_day = st.slider("Select Day", min_value=min_day, max_value=max_day, value=max_day)
            
            # Display a timeline of events for the selected day
            st.subheader(f"Day {selected_day} Events")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Display agent metrics for this day
                if not agents_df.empty:
                    day_agents = agents_df[agents_df['day'] == selected_day]
                    
                    st.metric("Active Agents", len(day_agents))
                    
                    # Check if need columns exist
                    need_cols = [col for col in day_agents.columns if col.startswith('need_')]
                    if need_cols:
                        avg_needs = {}
                        for col in need_cols:
                            need_name = col.replace('need_', '').capitalize()
                            avg_needs[need_name] = day_agents[col].mean()
                        
                        # Display needs in a nice format
                        st.subheader("Average Needs")
                        for need, value in avg_needs.items():
                            st.progress(value)
                            st.caption(f"{need}: {value:.2f}")
            
            with col2:
                # Show actions taken on this day
                if not action_counts_df.empty:
                    day_actions = action_counts_df[action_counts_df['day'] == selected_day]
                    
                    if not day_actions.empty:
                        st.subheader("Actions Taken")
                        
                        fig = px.pie(
                            day_actions,
                            values='count',
                            names='latest_action',
                            title=f'Day {selected_day} Actions'
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with col3:
                # Show creative output for this day
                creative_count = 0
                creative_items = []
                
                # Count ideas
                if not ideas_df.empty:
                    day_ideas = ideas_df[ideas_df['day'] == selected_day]
                    idea_count = len(day_ideas)
                    creative_count += idea_count
                    if idea_count > 0:
                        creative_items.append(f"{idea_count} ideas")
                
                # Count songs
                if not songs_df.empty:
                    day_songs = songs_df[songs_df['day'] == selected_day]
                    song_count = len(day_songs)
                    creative_count += song_count
                    if song_count > 0:
                        creative_items.append(f"{song_count} songs")
                
                # Count inventions
                if not inventions_df.empty:
                    day_inventions = inventions_df[inventions_df['day'] == selected_day]
                    invention_count = len(day_inventions)
                    creative_count += invention_count
                    if invention_count > 0:
                        creative_items.append(f"{invention_count} inventions")
                
                st.metric("Creative Outputs", creative_count)
                if creative_items:
                    st.write(", ".join(creative_items))
            
            # Create a detailed timeline of the day's events
            st.subheader("Day Detail Timeline")
            
            # Combine all events for this day into a single timeline
            timeline_events = []
            
            # Add agent actions
            if not agents_df.empty and 'latest_action' in agents_df.columns:
                day_agent_actions = agents_df[agents_df['day'] == selected_day]
                for _, agent in day_agent_actions.iterrows():
                    if pd.notna(agent.get('latest_action')):
                        event = {
                            'time': 'Day',
                            'agent': agent['agent_name'],
                            'event_type': agent['latest_action'],
                            'description': f"{agent['agent_name']} performed {agent['latest_action']}"
                        }
                        
                        # Add thoughts if available
                        if 'latest_thoughts' in agent and pd.notna(agent['latest_thoughts']):
                            event['details'] = agent['latest_thoughts']
                        
                        timeline_events.append(event)
            
            # Add ideas
            if not ideas_df.empty:
                day_ideas = ideas_df[ideas_df['day'] == selected_day]
                for _, idea in day_ideas.iterrows():
                    event = {
                        'time': 'Day',
                        'agent': idea['agent_name'],
                        'event_type': 'IDEA',
                        'description': f"{idea['agent_name']} had an idea",
                        'details': idea['idea_text']
                    }
                    timeline_events.append(event)
            
            # Add songs
            if not songs_df.empty:
                day_songs = songs_df[songs_df['day'] == selected_day]
                for _, song in day_songs.iterrows():
                    event = {
                        'time': 'Day',
                        'agent': song['composer_name'],
                        'event_type': 'SONG',
                        'description': f"{song['composer_name']} composed '{song['title']}' ({song['genre']})",
                        'details': f"Genre: {song['genre']}, BPM: {song['bpm']}"
                    }
                    timeline_events.append(event)
            
            # Add inventions
            if not inventions_df.empty:
                day_inventions = inventions_df[inventions_df['day'] == selected_day]
                for _, invention in day_inventions.iterrows():
                    event = {
                        'time': 'Day',
                        'agent': invention['inventor_name'],
                        'event_type': 'INVENTION',
                        'description': f"{invention['inventor_name']} invented '{invention['invention_name']}'",
                        'details': f"Type: {invention['invention_type']}, Quality: {invention['invention_quality']:.2f}"
                    }
                    timeline_events.append(event)
            
            # Add night activities
            if not night_activities_df.empty:
                day_night_activities = night_activities_df[night_activities_df['day'] == selected_day]
                for _, activity in day_night_activities.iterrows():
                    event_description = []
                    event_details = []
                    
                    if 'song_choice' in activity and pd.notna(activity['song_choice']):
                        event_description.append(f"listened to '{activity['song_choice']}'")
                    
                    if 'sent_letters' in activity and activity['sent_letters'] > 0:
                        recipient_info = f" to {activity['letter_recipient']}" if 'letter_recipient' in activity and pd.notna(activity['letter_recipient']) else ""
                        event_description.append(f"sent letter{recipient_info}")
                        
                        if 'letter_title' in activity and pd.notna(activity['letter_title']):
                            event_details.append(f"Letter title: {activity['letter_title']}")
                    
                    if 'dinner_items' in activity and activity['dinner_items'] > 0:
                        event_description.append("had dinner")
                        
                        if 'avg_dinner_quality' in activity and pd.notna(activity['avg_dinner_quality']):
                            event_details.append(f"Dinner quality: {activity['avg_dinner_quality']:.2f}")
                    
                    if event_description:
                        event = {
                            'time': 'Night',
                            'agent': activity['agent_name'],
                            'event_type': 'NIGHT',
                            'description': f"{activity['agent_name']} " + " and ".join(event_description),
                            'details': "; ".join(event_details) if event_details else None
                        }
                        timeline_events.append(event)
            
            # Sort and display timeline events
            if timeline_events:
                # Sort by time (day/night) and then by agent name for readability
                timeline_events.sort(key=lambda x: (0 if x['time'] == 'Day' else 1, x['agent']))
                
                # Display in an easy-to-read format
                for event in timeline_events:
                    with st.expander(f"**{event['time']}**: {event['description']}"):
                        if 'details' in event and event['details']:
                            st.write(event['details'])
            else:
                st.info(f"No recorded events for day {selected_day}")
        else:
            st.warning("No timeline data available.")


# Main function
def main():
    """Main function to run the Streamlit dashboard"""
    
    # Check if refresh button was clicked
    if st.session_state.get('refresh_clicked', False):
        # Clear cached data to force reload
        load_settlement_data.clear()
        st.session_state['refresh_clicked'] = False
        st.success("Data refreshed successfully!")
    
    # Track refresh button click
    if 'refresh_clicked' not in st.session_state:
        st.session_state['refresh_clicked'] = False
    
    # Handle refresh button click
    if refresh_data:
        st.session_state['refresh_clicked'] = True
        st.experimental_rerun()
    
    # Load data with loading indicator
    with st.spinner("Loading settlement data..."):
        data = load_settlement_data(data_dir)

    if not data:
        st.error("No data files found. Please check the data directory.")
        return

    # Process data with loading indicator
    with st.spinner("Processing data..."):
        processed_data = process_settlement_data(data)

    # Setup data download in sidebar
    with st.sidebar:
        st.subheader("Data Export")
        
        # Only show download buttons if we have data
        if processed_data:
            # Create tabs for different data types to download
            download_tabs = st.tabs(["Agents", "Economy", "Culture"])
            
            with download_tabs[0]:
                if not processed_data.get('agents_df', pd.DataFrame()).empty:
                    csv = processed_data['agents_df'].to_csv(index=False)
                    st.download_button(
                        label="Download Agent Data",
                        data=csv,
                        file_name="agent_data.csv",
                        mime="text/csv",
                    )
            
            with download_tabs[1]:
                if not processed_data.get('market_df', pd.DataFrame()).empty:
                    csv = processed_data['market_df'].to_csv(index=False)
                    st.download_button(
                        label="Download Market Data",
                        data=csv,
                        file_name="market_data.csv",
                        mime="text/csv",
                    )
            
            with download_tabs[2]:
                col1, col2 = st.columns(2)
                
                with col1:
                    if not processed_data.get('ideas_df', pd.DataFrame()).empty:
                        csv = processed_data['ideas_df'].to_csv(index=False)
                        st.download_button(
                            label="Download Ideas",
                            data=csv,
                            file_name="ideas_data.csv",
                            mime="text/csv",
                        )
                
                with col2:
                    if not processed_data.get('songs_df', pd.DataFrame()).empty:
                        csv = processed_data['songs_df'].to_csv(index=False)
                        st.download_button(
                            label="Download Songs",
                            data=csv,
                            file_name="songs_data.csv",
                            mime="text/csv",
                        )
                
                if not processed_data.get('inventions_df', pd.DataFrame()).empty:
                    csv = processed_data['inventions_df'].to_csv(index=False)
                    st.download_button(
                        label="Download Inventions",
                        data=csv,
                        file_name="inventions_data.csv",
                        mime="text/csv",
                    )
    
    # Create dashboard
    create_dashboard(processed_data)


if __name__ == "__main__":
    main()
