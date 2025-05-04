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
    st.divider()
    st.markdown("**Made for 2993 Mars Settlement Agency**")


# Data Loading Function
@st.cache_data
def load_settlement_data(data_directory):
    """Load all state files and history from the given directory"""
    all_data = {}
    # Find all day_*_state.json files
    state_files = glob.glob(os.path.join(data_directory, "day_*_state.json"))
    for file_path in state_files:
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Extract day number from filename
                day_num = int(re.search(r'day_(\d+)_state', file_path).group(1))
                all_data[day_num] = data
        except Exception as e:
            st.error(f"Error loading {file_path}: {str(e)}")

    # Also check for history.json if it exists
    history_path = os.path.join(data_directory, "history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, 'r') as f:
                history_data = json.load(f)
                all_data['history'] = history_data
        except Exception as e:
            st.error(f"Error loading history.json: {str(e)}")

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
            day_data: SimulationState = SimulationState.model_validate(data[day])
        except ValidationError as exc:
            raise exc

        # Process agents
        for agent in day_data.agents:
            agent_id = agent.id
            agent_name = agent.name
            agent.goods = [Good(**g) for g in agent.goods]

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
            needs = agent.needs
            for need_type, value in needs.items():
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
            history = agent.history
            if history:
                print("HIST...")
                latest_action = history[-1]
                print(f"ACT...{latest_action}")
                if isinstance(latest_action, tuple) and len(latest_action) >= 4:
                    action_data = latest_action[3]
                    if isinstance(action_data, dict):
                        agent_row['latest_action'] = action_data['type']

                        # Extract thoughts if available
                        if 'extras' in action_data and 'thoughts' in action_data['extras']:
                            thoughts = action_data['extras']['thoughts']
                            if isinstance(thoughts, str) and thoughts.strip():
                                agent_row['latest_thoughts'] = thoughts

            agent_data.append(agent_row)

        # Process market listings
        for listing in day_data.market.listings:
            market_row = {
                'day': day,
                'listing_id': listing.id,
                'seller_id': listing.seller_id,
                'price': listing.price,
                'listed_on_day': listing.listed_on_day,
            }

            if 'good' in listing:
                good = listing['good']
                market_row['good_type'] = good.get('type', 'UNKNOWN')
                market_row['good_name'] = good.get('name', 'Unknown Item')
                market_row['good_quality'] = good.get('quality', 0)

            market_data.append(market_row)

        # Process ideas
        day_ideas = day_data.ideas[day]
        for idea in day_ideas:
            agent = idea[0]
            thought = idea[1]
            if isinstance(idea, list) and len(idea) > 1:
                idea_row = {
                    'day': day,
                    'agent_id': agent.id,
                    'agent_name': agent.name,
                    'idea_text': thought,
                }
                ideas_data.append(idea_row)

        # Process songs
        day_songs = day_data.songs
        genres = day_songs.genres
        history_data = day_songs.history_data
        # lets use history_data: Dict[int, List[SongEntry]] 
        # class SongEntry(BaseModel):
        #     agent: "Agent"
        #     song: Song
        #     day: int

        # class Song(BaseModel):
        #     title: str
        #     genre: str = "Electronica"
        #     bpm: int = Field(default=113)
        #     tags: List[str] = []
        #     description: Optional[str] = None

        for day, songs_list in history_data.items():
            for entry in songs_list:
                song_row = {
                    'day': day,
                    'genre': entry.song.genre,
                    'title': entry.song.title,
                    'composer_id': entry.agent.id,
                    'composer_name': entry.agent.name,
                    'bpm': entry.song.bpm,
                }
                songs_data.append(song_row)

        # Process inventions
        day_inventions = day_data.inventions
        for invention in day_inventions:
            if isinstance(invention, list) and len(invention) > 1:
                invention_row = {
                    'day': day,
                    'inventor_id': invention[0].get('id', 'unknown') if isinstance(invention[0], dict) else 'unknown',
                    'inventor_name': invention[0].get('name', 'Unknown Inventor') if isinstance(invention[0],
                                                                                                dict) else 'Unknown',
                    'invention_type': invention[1].get('type', 'UNKNOWN') if isinstance(invention[1],
                                                                                        dict) else 'UNKNOWN',
                    'invention_name': invention[1].get('name', 'Unknown Item') if isinstance(invention[1],
                                                                                             dict) else 'Unknown',
                    'invention_quality': invention[1].get('quality', 0) if isinstance(invention[1], dict) else 0,
                }
                inventions_data.append(invention_row)

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

    return processed


# Create the main dashboard
def create_dashboard(processed_data):
    """Create the main dashboard with tabs for different aspects"""
    # Create tabs
    tabs = st.tabs(["Overview", "Agents", "Economy", "Culture", "Society Evolution"])

    # Get DataFrames
    agents_df = processed_data.get('agents_df', pd.DataFrame())
    market_df = processed_data.get('market_df', pd.DataFrame())
    ideas_df = processed_data.get('ideas_df', pd.DataFrame())
    songs_df = processed_data.get('songs_df', pd.DataFrame())
    inventions_df = processed_data.get('inventions_df', pd.DataFrame())
    action_counts_df = processed_data.get('action_counts_df', pd.DataFrame())
    days = processed_data.get('days', [])

    # Overview Tab
    with tabs[0]:
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

    # Agents Tab
    with tabs[1]:
        if show_agent_details:
            st.header("Agent Analytics")

            # Agent selector
            agent_ids = sorted(agents_df['agent_id'].unique()) if not agents_df.empty else []
            selected_agent = st.selectbox("Select Agent", agent_ids, format_func=lambda x:
            agents_df[agents_df['agent_id'] == x]['agent_name'].iloc[0] if len(
                agents_df[agents_df['agent_id'] == x]) > 0 else x)

            if selected_agent and not agents_df.empty:
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
            else:
                st.write("No agent data available.")
        else:
            st.info("Enable 'Show Agent Details' in the sidebar to view agent analytics.")

    # Economy Tab
    with tabs[2]:
        if show_economy:
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
        else:
            st.info("Enable 'Show Economy' in the sidebar to view economic analytics.")

    # Culture Tab
    with tabs[3]:
        if show_culture:
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
        else:
            st.info("Enable 'Show Culture' in the sidebar to view cultural analytics.")

    # Society Evolution Tab
    with tabs[4]:
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


# Main function
def main():
    # Load data
    data = load_settlement_data(data_dir)

    if not data:
        st.error("No data files found. Please check the data directory.")
        return

    # Process data
    processed_data = process_settlement_data(data)

    # Create dashboard
    create_dashboard(processed_data)


if __name__ == "__main__":
    main()
