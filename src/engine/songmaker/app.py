import streamlit as st
import random
import time
import uuid
import json
from datetime import datetime
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import List, Dict, Set, Optional, Tuple
import threading
import queue

# Import from models
from src.models.simulation import Song, SongBook
from src.engine.songmaker.models.genre_graph import GenreGraph, genre_graph
from src.engine.songmaker.generators.title_generator import TitleGenerator
from src.engine.songmaker.generators.description_generator import DescriptionGenerator

# Initialize generators
title_generator = TitleGenerator()
description_generator = DescriptionGenerator()

# Set page configuration
st.set_page_config(
    page_title="Song Generator",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply dark theme styling
st.markdown("""
<style>
    :root {
        --primary-color: #ff00ff;
        --background-color: #0f1117;
        --secondary-background-color: #1a1c24;
        --text-color: #f0f2f6;
        --font: 'Orbitron', sans-serif;
    }
    
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    .sidebar .sidebar-content {
        background-color: var(--secondary-background-color);
    }
    
    h1, h2, h3 {
        color: #00ffaa;
        font-family: var(--font);
    }
    
    .stButton button {
        background-color: #ff00aa;
        color: white;
        border: none;
        border-radius: 5px;
    }
    
    .stButton button:hover {
        background-color: #ff00ff;
    }
    
    .neon-box {
        border: 2px solid #00ffaa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 0 10px #00ffaa;
    }
    
    .neon-text {
        color: #00ffaa;
        text-shadow: 0 0 5px #00ffaa;
    }
    
    .neon-pink {
        color: #ff00aa;
        text-shadow: 0 0 5px #ff00aa;
    }
    
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    * {
        font-family: 'Orbitron', sans-serif;
    }
</style>
""", unsafe_allow_html=True)

# Data storage and initialization
SAVE_PATH = "song_data.json"

class SongGenerator:
    def __init__(self):
        self.songbook = SongBook()
        self.popular_tags = set(["electronic", "future", "cyber", "neon", "digital", "synth"])
        self.songs_count = 0
        self.auto_generation_active = False
        self.auto_generation_thread = None
        self.auto_queue = queue.Queue()
        
        # User character profile
        self.producer_name = "Anonymous Producer"
        self.producer_age = 30
        self.producer_style = "Creative music producer"
        self.producer_backstory = "A mysterious artist emerging from the neon-lit streets of the cyberpunk underground."
        
        # Unlockable features and progression system
        self.unlockables = {
            "auto_generation": {"name": "Auto Generation", "required_songs": 5, "unlocked": False, 
                              "description": "Automatically generate songs over time"},
            "description_generator": {"name": "Description Generator", "required_songs": 3, "unlocked": False,
                                    "description": "Generate professional-sounding track descriptions"},
            "genre_fusion": {"name": "Genre Fusion", "required_songs": 10, "unlocked": False,
                           "description": "Create new genre combinations"},
            "theme_customizer": {"name": "Theme Customizer", "required_songs": 15, "unlocked": False,
                               "description": "Customize your studio's appearance"},
            "advanced_analytics": {"name": "Advanced Analytics", "required_songs": 20, "unlocked": False,
                                 "description": "Access detailed stats about your music"},
        }
        
        # Credits/currency system
        self.credits = 0
        self.credit_multiplier = 1.0
        
        # Achievements and stats
        self.achievements = {
            "songs_created": {"name": "Song Creator", "levels": [1, 5, 10, 25, 50, 100], "current_level": 0},
            "genres_discovered": {"name": "Genre Explorer", "levels": [1, 3, 5, 10, 15, 20], "current_level": 0},
            "tags_used": {"name": "Tag Master", "levels": [5, 10, 20, 30, 50, 100], "current_level": 0},
        }
        self.total_tags_used = set()
        self.day = 1
        
        # Load data if exists
        self.load_data()
        
        # Check for unlockables based on loaded data
        self.update_unlockables()
        
    def save_data(self):
        """Save song data to a JSON file"""
        data = {
            "genres": genre_graph.get_all_genres(),
            "popular_tags": list(self.popular_tags),
            "songs_count": self.songs_count,
            "total_tags_used": list(self.total_tags_used),
            "achievements": self.achievements,
            "day": self.day,
            "song_history": {},
            "producer_profile": {
                "name": self.producer_name,
                "age": self.producer_age,
                "style": self.producer_style,
                "backstory": self.producer_backstory
            },
            "unlockables": self.unlockables,
            "credits": self.credits,
            "credit_multiplier": self.credit_multiplier
        }
        
        # Convert SongBook to serializable format
        for day, entries in self.songbook.history_data.items():
            data["song_history"][day] = []
            for entry in entries:
                song_data = {
                    "title": entry.song.title,
                    "genre": entry.song.genre,
                    "bpm": entry.song.bpm,
                    "tags": entry.song.tags,
                    "description": entry.song.description,
                }
                data["song_history"][day].append(song_data)
        
        # Save to file
        with open(SAVE_PATH, "w") as f:
            json.dump(data, f)
            
    def load_data(self):
        """Load song data from a JSON file if it exists"""
        try:
            if Path(SAVE_PATH).exists():
                with open(SAVE_PATH, "r") as f:
                    data = json.load(f)
                
                self.popular_tags = set(data.get("popular_tags", ["electronic", "future", "cyber", "neon", "digital", "synth"]))
                self.songs_count = data.get("songs_count", 0)
                self.total_tags_used = set(data.get("total_tags_used", []))
                self.achievements = data.get("achievements", self.achievements)
                self.day = data.get("day", 1)
                
                # Load producer profile if it exists
                if "producer_profile" in data:
                    self.producer_name = data["producer_profile"].get("name", self.producer_name)
                    self.producer_age = data["producer_profile"].get("age", self.producer_age)
                    self.producer_style = data["producer_profile"].get("style", self.producer_style)
                    self.producer_backstory = data["producer_profile"].get("backstory", self.producer_backstory)
                
                # Load unlockables and credit system
                if "unlockables" in data:
                    self.unlockables = data["unlockables"]
                if "credits" in data:
                    self.credits = data["credits"]
                if "credit_multiplier" in data:
                    self.credit_multiplier = data["credit_multiplier"]
                
                # Load song history
                song_history = data.get("song_history", {})
                for day_str, song_entries in song_history.items():
                    day = int(day_str)
                    for song_data in song_entries:
                        song = Song(
                            title=song_data["title"],
                            genre=song_data["genre"],
                            bpm=song_data["bpm"],
                            tags=song_data["tags"],
                            description=song_data.get("description", None)
                        )
                        # Create a dummy agent for the songbook
                        # We're using the Agent class minimally just to maintain compatibility
                        from src.models.agent import Agent, AgentPersonality, AgentNeeds
                        dummy_agent = Agent(
                            name=self.producer_name,
                            age=self.producer_age,
                            personality=AgentPersonality(text=self.producer_style),
                            needs=AgentNeeds()
                        )
                        self.songbook.add_song(dummy_agent, song, day)
        except Exception as e:
            st.error(f"Error loading data: {e}")

    def update_unlockables(self):
        """Update which features are unlocked based on songs count"""
        for feature_id, feature in self.unlockables.items():
            if self.songs_count >= feature["required_songs"]:
                feature["unlocked"] = True
                
    def add_credits(self, amount: int):
        """Add credits with multiplier applied"""
        self.credits += amount * self.credit_multiplier
        self.save_data()

    def update_achievements(self):
        """Update achievements based on stats"""
        # Songs created achievement
        songs_count = self.songs_count
        for i, level in enumerate(self.achievements["songs_created"]["levels"]):
            if songs_count >= level:
                self.achievements["songs_created"]["current_level"] = i + 1
        
        # Genres discovered achievement
        genres_count = len(genre_graph.get_all_genres())
        for i, level in enumerate(self.achievements["genres_discovered"]["levels"]):
            if genres_count >= level:
                self.achievements["genres_discovered"]["current_level"] = i + 1
        
        # Tags used achievement
        tags_count = len(self.total_tags_used)
        for i, level in enumerate(self.achievements["tags_used"]["levels"]):
            if tags_count >= level:
                self.achievements["tags_used"]["current_level"] = i + 1
    
    def generate_random_song(self) -> Song:
        """Generate a random song using advanced generators"""
        # Using GenreGraph to determine the genre
        if random.random() < 0.2:
            # Create a new genre fusion 
            genre_name, _ = genre_graph.create_genre_fusion()
            genre = genre_name
        else:
            # Use existing genre
            genre = genre_graph.get_next_genre()
        
        # Use TitleGenerator to create a title
        style_bias = None
        if "cyberpunk" in genre.lower():
            style_bias = "cyberpunk"
        elif "vapor" in genre.lower():
            style_bias = "vaporwave"
        
        title = title_generator.generate_title(style_bias)
        
        # Generate BPM (60-180)
        bpm = random.randint(60, 180)
        
        # Generate tags (3-6 random tags)
        available_tags = list(self.popular_tags)
        num_tags = random.randint(3, 6)
        if len(available_tags) < num_tags:
            # Create some new tags if we don't have enough
            possible_new_tags = ["futuristic", "dystopian", "utopian", "retro", "glitch", "holographic", 
                                "immersive", "neural", "quantum", "virtual", "augmented", "synthetic", 
                                "organic", "mechanical", "industrial", "ethereal", "ambient", "dark", 
                                "bright", "melodic", "rhythmic", "atmospheric", "experimental"]
            for _ in range(num_tags - len(available_tags)):
                available_tags.append(random.choice(possible_new_tags))
            
        tags = random.sample(available_tags, num_tags)
        
        # Add tags to total tags used
        for tag in tags:
            self.total_tags_used.add(tag)
            self.popular_tags.add(tag)
        
        # Generate a description
        description = description_generator.generate_description(genre, tags)
        
        # Create song
        return Song(
            title=title,
            genre=genre,
            bpm=bpm,
            tags=tags,
            description=description
        )
    
    def add_song(self, song: Song):
        """Add a song to the songbook"""
        from src.models.agent import Agent, AgentPersonality, AgentNeeds
        dummy_agent = Agent(
            name=self.producer_name,
            age=self.producer_age,
            personality=AgentPersonality(text=self.producer_style),
            needs=AgentNeeds()
        )
        self.songbook.add_song(dummy_agent, song, self.day)
        self.songs_count += 1
        
        for tag in song.tags:
            self.total_tags_used.add(tag)
            self.popular_tags.add(tag)
        
        # Award credits and XP
        credits_earned = 10 + random.randint(1, 5)
        self.add_credits(credits_earned)
        
        # Update achievements and unlockables
        self.update_achievements()
        self.update_unlockables()
        self.save_data()
        
        return credits_earned
    
    def auto_generate_songs(self, stop_event):
        """Auto-generate songs every few seconds"""
        while not stop_event.is_set():
            song = self.generate_random_song()
            self.auto_queue.put(song)
            time.sleep(random.uniform(1.5, 3.0))  # Random time between 1.5 and 3 seconds
    
    def start_auto_generation(self):
        """Start auto-generating songs"""
        if not self.auto_generation_active:
            self.auto_generation_active = True
            self.stop_event = threading.Event()
            self.auto_generation_thread = threading.Thread(
                target=self.auto_generate_songs, 
                args=(self.stop_event,)
            )
            self.auto_generation_thread.daemon = True
            self.auto_generation_thread.start()
    
    def stop_auto_generation(self):
        """Stop auto-generating songs"""
        if self.auto_generation_active:
            self.stop_event.set()
            self.auto_generation_active = False
    
    def process_queue(self):
        """Process the auto-generation queue"""
        if self.auto_generation_active:
            try:
                while not self.auto_queue.empty():
                    song = self.auto_queue.get_nowait()
                    credits_earned = self.add_song(song)
                    self.auto_queue.task_done()
            except queue.Empty:
                pass
    
    def advance_day(self):
        """Advance to the next day"""
        self.day += 1
        self.save_data()
        return self.day

# Initialize the song generator
@st.cache_resource
def get_song_generator():
    return SongGenerator()

song_generator = get_song_generator()

# Process any auto-generated songs
if song_generator.auto_generation_active:
    song_generator.process_queue()

# Create the UI
st.markdown("<h1 class='neon-text'>🎵 CYBER SONG GENERATOR 🎵</h1>", unsafe_allow_html=True)

# Main layout
col1, col2 = st.columns([2, 3])

# Left column - Control Panel
with col1:
    st.markdown("<div class='neon-box'>", unsafe_allow_html=True)
    st.markdown("<h2 class='neon-pink'>Control Panel</h2>", unsafe_allow_html=True)
    
    # Producer Profile
    with st.expander("Producer Profile", expanded=False):
        with st.form("producer_profile_form"):
            st.write("Edit your producer profile")
            producer_name = st.text_input("Producer Name", value=song_generator.producer_name)
            producer_age = st.number_input("Age", min_value=16, max_value=100, value=song_generator.producer_age)
            producer_style = st.text_input("Producer Style", value=song_generator.producer_style)
            producer_backstory = st.text_area("Backstory", value=song_generator.producer_backstory)
            
            if st.form_submit_button("Update Profile"):
                song_generator.producer_name = producer_name
                song_generator.producer_age = producer_age
                song_generator.producer_style = producer_style
                song_generator.producer_backstory = producer_backstory
                song_generator.save_data()
                st.success("Profile updated!")
    
    # Manual song creation
    with st.form("song_creation_form"):
        st.write("Create a new song")
        title = st.text_input("Song Title", key="title_input", value="Neon Dreams")
        
        # Genre selection with option to create new
        genre_options = genre_graph.get_all_genres()
        genre_options.append("+ Create New Genre")
        genre_selection = st.selectbox("Genre", genre_options, key="genre_select")
        
        if genre_selection == "+ Create New Genre":
            new_genre = st.text_input("New Genre Name", key="new_genre_input")
            if new_genre:
                genre = new_genre
            else:
                genre = "Electronica"  # Default if no new genre entered
        else:
            genre = genre_selection
        
        bpm = st.slider("BPM", min_value=60, max_value=180, value=120, step=1, key="bpm_slider")
        
        # Tags selection
        available_tags = list(song_generator.popular_tags)
        tags = st.multiselect("Tags", available_tags, default=random.sample(available_tags, min(3, len(available_tags))), key="tags_select")
        
        # Option to add new tag
        new_tag = st.text_input("Add New Tag", key="new_tag_input")
        
        # Description field
        description = st.text_area("Description (Optional)", key="description_input")
        
        # Generate description button replaced with checkbox
        generate_desc = st.checkbox("Generate random description", key="gen_desc_checkbox")
        
        # Submit button
        submitted = st.form_submit_button("Create Song", type="primary")
        
        if submitted:
            # If checkbox is checked, generate a description
            if generate_desc:
                description = description_generator.generate_description(genre, tags)
            
            # Add new tag if one was entered
            if new_tag:
                tags.append(new_tag)
                song_generator.popular_tags.add(new_tag)
            
            if not title:
                st.error("Song title is required!")
            elif not genre:
                st.error("Genre is required!")
            elif not tags:
                st.error("At least one tag is required!")
            else:
                # Create the song
                song = Song(
                    title=title,
                    genre=genre,
                    bpm=bpm,
                    tags=tags,
                    description=description if description else None
                )
                
                # If new genre, add it to the graph
                if genre not in genre_graph.get_all_genres():
                    genre_node = genre_graph.add_genre(genre)
                    genre_graph.add_connections_for_new_genre(genre)
                
                credits_earned = song_generator.add_song(song)
                st.success(f"Created new song: {song.title} (+{credits_earned} credits)")

    # Auto generation control
    st.markdown("<h3>Auto Generation</h3>", unsafe_allow_html=True)
    auto_gen_col1, auto_gen_col2 = st.columns(2)
    
    # Check if auto generation is unlocked
    auto_gen_unlocked = song_generator.unlockables["auto_generation"]["unlocked"]

    with auto_gen_col1:
        if not auto_gen_unlocked:
            st.warning("Unlock this feature by creating 5 songs")
        elif not song_generator.auto_generation_active:
            if st.button("Start Auto Generation", key="start_auto_btn"):
                song_generator.start_auto_generation()
                st.rerun()
        else:
            if st.button("Stop Auto Generation", key="stop_auto_btn"):
                song_generator.stop_auto_generation()
                st.rerun()
    
    with auto_gen_col2:
        if st.button("Generate Random Song", key="random_song_btn"):
            song = song_generator.generate_random_song()
            credits_earned = song_generator.add_song(song)
            st.success(f"Generated new song: {song.title} (+{credits_earned} credits)")
            st.rerun()
    
    # Calendar navigation
    st.markdown("<h3>Day Navigation</h3>", unsafe_allow_html=True)
    st.write(f"Current Day: {song_generator.day}")
    
    if st.button("Advance to Next Day", key="next_day_btn"):
        new_day = song_generator.advance_day()
        st.success(f"Advanced to Day {new_day}")
        st.rerun()
    
    # Achievements section
    st.markdown("<h3 class='neon-text'>Achievements</h3>", unsafe_allow_html=True)
    
    for achievement_key, achievement in song_generator.achievements.items():
        current_level = achievement["current_level"]
        max_level = len(achievement["levels"])
        
        # Calculate progress
        if current_level < max_level:
            next_level_target = achievement["levels"][current_level]
            if achievement_key == "songs_created":
                current_value = song_generator.songs_count
            elif achievement_key == "genres_discovered":
                current_value = len(genre_graph.get_all_genres())
            elif achievement_key == "tags_used":
                current_value = len(song_generator.total_tags_used)
            else:
                current_value = 0
                
            progress = min(1.0, current_value / next_level_target)
        else:
            progress = 1.0
            
        # Display achievement
        st.write(f"{achievement['name']} - Level {current_level}/{max_level}")
        st.progress(progress)

    # Unlockables section
    st.markdown("<h3 class='neon-text'>Studio Upgrades</h3>", unsafe_allow_html=True)
    st.write(f"Credits: {int(song_generator.credits)} 💰")

    for feature_id, feature in song_generator.unlockables.items():
        unlocked = feature["unlocked"]
        name = feature["name"]
        required = feature["required_songs"]
        description = feature["description"]
        
        # Calculate progress
        progress = min(1.0, song_generator.songs_count / required)
        
        # Create colored status indicator
        if unlocked:
            status = "🟢 UNLOCKED"
            status_color = "#00ff00"
        else:
            status = f"🔒 LOCKED (Need {required} songs)"
            status_color = "#ff0000"
        
        # Display feature with status
        st.write(f"**{name}**: {description}")
        st.write(f"<span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)
        st.progress(progress)

    st.markdown("</div>", unsafe_allow_html=True)

# Right column - Stats and Visualization
with col2:
    st.markdown("<div class='neon-box'>", unsafe_allow_html=True)
    st.markdown("<h2 class='neon-text'>Song Library</h2>", unsafe_allow_html=True)
    
    # Song list
    song_data = []
    for day, entries in song_generator.songbook.history_data.items():
        for entry in entries:
            song_data.append({
                "Day": day,
                "Title": entry.song.title,
                "Genre": entry.song.genre,
                "BPM": entry.song.bpm,
                "Tags": ", ".join(entry.song.tags),
            })
    
    if song_data:
        df = pd.DataFrame(song_data)
        st.dataframe(df, use_container_width=True, height=200)
    else:
        st.info("No songs created yet. Start creating songs to fill your library!")
    
    # Visualization tabs
    viz_tab1, viz_tab2, viz_tab3 = st.tabs(["Genre Distribution", "Tag Cloud", "BPM Analysis"])
    
    with viz_tab1:
        if song_data:
            # Genre distribution chart
            genre_counts = {}
            for day, entries in song_generator.songbook.history_data.items():
                for entry in entries:
                    genre = entry.song.genre
                    if genre in genre_counts:
                        genre_counts[genre] += 1
                    else:
                        genre_counts[genre] = 1
            
            # Create genre data
            genre_df = pd.DataFrame({
                "Genre": list(genre_counts.keys()),
                "Count": list(genre_counts.values())
            }).sort_values("Count", ascending=False)
            
            # Plot
            fig = px.bar(
                genre_df, 
                x="Genre", 
                y="Count", 
                title="Genre Distribution",
                color="Count",
                color_continuous_scale="Viridis"
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1a1c24",
                plot_bgcolor="#1a1c24",
                font=dict(family="Orbitron, sans-serif", color="#00ffaa"),
                title_font=dict(family="Orbitron, sans-serif", color="#00ffaa"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Create some songs to see genre distribution.")
    
    with viz_tab2:
        if song_data:
            # Tag cloud
            all_tags = []
            for day, entries in song_generator.songbook.history_data.items():
                for entry in entries:
                    all_tags.extend(entry.song.tags)
            
            # Count tag frequencies
            tag_freq = {}
            for tag in all_tags:
                if tag in tag_freq:
                    tag_freq[tag] += 1
                else:
                    tag_freq[tag] = 1
            
            # Generate wordcloud
            if tag_freq:
                # Use a custom color function for neon colors
                def neon_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
                    colors = ["#00ffaa", "#ff00aa", "#00aaff", "#ffaa00", "#aa00ff"]
                    return random.choice(colors)
                
                wc = WordCloud(
                    background_color="#1a1c24",
                    width=800,
                    height=400,
                    max_words=100,
                    color_func=neon_color_func,
                    contour_width=1,
                    contour_color="#00ffaa"
                ).generate_from_frequencies(tag_freq)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wc, interpolation='bilinear')
                ax.axis("off")
                ax.set_facecolor("#1a1c24")
                fig.patch.set_facecolor("#1a1c24")
                st.pyplot(fig)
            else:
                st.info("Add tags to your songs to generate a tag cloud.")
        else:
            st.info("Create some songs to see the tag cloud.")
    
    with viz_tab3:
        if song_data:
            # BPM Analysis
            bpm_data = []
            for day, entries in song_generator.songbook.history_data.items():
                for entry in entries:
                    bpm_data.append({
                        "Title": entry.song.title,
                        "BPM": entry.song.bpm,
                        "Genre": entry.song.genre,
                        "Day": day
                    })
            
            bpm_df = pd.DataFrame(bpm_data)
            
            # BPM histogram
            fig1 = px.histogram(
                bpm_df, 
                x="BPM", 
                nbins=20, 
                title="BPM Distribution",
                color_discrete_sequence=["#00ffaa"]
            )
            fig1.update_layout(
                template="plotly_dark",
                paper_bgcolor="#1a1c24",
                plot_bgcolor="#1a1c24",
                font=dict(family="Orbitron, sans-serif", color="#00ffaa"),
                title_font=dict(family="Orbitron, sans-serif", color="#00ffaa"),
            )
            st.plotly_chart(fig1, use_container_width=True)
            
            # BPM by genre
            if len(bpm_df) >= 3:  # Only show if we have enough data
                fig2 = px.box(
                    bpm_df, 
                    x="Genre", 
                    y="BPM", 
                    title="BPM by Genre",
                    color="Genre",
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig2.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#1a1c24",
                    plot_bgcolor="#1a1c24",
                    font=dict(family="Orbitron, sans-serif", color="#00ffaa"),
                    title_font=dict(family="Orbitron, sans-serif", color="#00ffaa"),
                )
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Create some songs to see BPM analysis.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Footer with stats
st.markdown("<div class='neon-box'>", unsafe_allow_html=True)
stats_col1, stats_col2, stats_col3, stats_col4, stats_col5 = st.columns(5)

with stats_col1:
    st.metric("Total Songs", song_generator.songs_count)

with stats_col2:
    st.metric("Unique Genres", len(genre_graph.get_all_genres()))

with stats_col3:
    st.metric("Unique Tags", len(song_generator.total_tags_used))

with stats_col4:
    songs_today = len(song_generator.songbook.day(song_generator.day))
    st.metric("Songs Today", songs_today)

with stats_col5:
    st.metric("Credits", int(song_generator.credits), delta="+10-15 per song")

st.markdown("</div>", unsafe_allow_html=True)

# Run the auto-generation processing again at the end to catch any songs generated during page interaction
if song_generator.auto_generation_active:
    song_generator.process_queue()

if __name__ == "__main__":
    # This allows the app to be run standalone with `streamlit run app.py`
    pass 