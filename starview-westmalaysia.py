"""
Advanced GeoAI Agent - StarView West Malaysia Site Selection
=============================================================
CYBERPUNK EDITION v3.2.7: Futuristic UI + OSM Up-to-Date + INSTANT Results

FOCUSED ON: BEST STARGAZING & GALAXY VIEWING SPOTS IN PENINSULAR MALAYSIA 🌌

V3.2.7 FIXES (NEW):
- ✅ WAQI distance validation: rejects stations >100km away (fixes Shanghai-for-Ampang bug)
- ✅ Station distance displayed in cross-check card
- ✅ Graceful rejection notice when no nearby station
- ✅ Ground-verified badge only shown for validated stations
- ✅ Full audit trail in CSV/JSON exports

V3.2.6 FIXES (preserved):
- ✅ WAQI integration: Cross-check Open-Meteo CAMS against DOE ground stations
- ✅ "Take higher" rule: uses more conservative PM2.5 for safety
- ✅ Source labeling shows ground-station verification when available
- ✅ Air Quality Cross-Check card (new expander)
- ✅ Graceful fallback if WAQI unavailable

V3.2.5 FIXES (preserved):
- ✅ Gunung Nuang elevation corrected (1,493m peak instead of 53m foothill)
- ✅ Protected zone radius tuned (Gunung Nuang: 15km → 6km, prevents false positives)
- ✅ Auto peak elevation detection for any name containing "Gunung"
- ✅ Protected zone inside/near distinction with strict inner radius
- ✅ Ampang/Port Klang coastal distance corrected
- ✅ Refined haze confidence levels

V3.2.4 FIXES (preserved):
- ✅ Elevation fallback for curated candidate sites (Gunung Nuang, Genting, etc.)
- ✅ Fixed HAZE card HTML rendering bug (raw <div> showing as text)

V3.2.3 FIXES (preserved):
- 🌴 Tropical Highland Fog Detection (Cameron, Genting, Fraser's Hill)
- ✅ Uses humidity + clean-air + low-visibility as primary signals

V3.2.2 FEATURES (preserved):
- 🌫️ High-Altitude Fog Detection
- ✅ Clean-air health advisory for natural fog

V3.2.1 FIXES (preserved):
- ✅ Coastal cloud risk classifier

V3.2 FEATURES (preserved):
- 🌫️ Haze Detection
- 📊 Live Air Quality Index (AQI)
- 💨 PM2.5, PM10, aerosol data
- 📅 Seasonal haze calendar for Malaysia

V3.1 FIXES (preserved):
- ✅ Population-weighted light pollution

V3.0 FEATURES (preserved):
- 🌙 Moon Phase Integration
- 🌌 Milky Way Visibility Calendar
- 📸 Astrophotography Score
- 📊 Export Reports
"""

import streamlit as st
import folium
from folium.plugins import Fullscreen, MiniMap, MousePosition
from streamlit_folium import st_folium
import pandas as pd
import numpy as np
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import requests
from pathlib import Path
import sqlite3
import pickle
import math

# ============================================================================
# CYBERPUNK STYLING (unchanged)
# ============================================================================

CYBERPUNK_CSS = """
<style>
    :root {
        --neon-cyan: #00f0ff;
        --neon-pink: #ff2d95;
        --neon-purple: #b026ff;
        --neon-green: #39ff14;
        --neon-yellow: #ffe84d;
    }
    .stApp {
        background: linear-gradient(135deg, #0a0a0f 0%, #1a0a2e 50%, #0a0a1f 100%);
    }
    .main-title {
        font-family: 'Courier New', monospace;
        font-size: 3.5rem;
        font-weight: 900;
        background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 4px;
        animation: glowPulse 3s ease-in-out infinite;
    }
    @keyframes glowPulse {
        0%, 100% { text-shadow: 0 0 40px rgba(0, 240, 255, 0.3); }
        50% { text-shadow: 0 0 60px rgba(0, 240, 255, 0.6), 0 0 80px rgba(176, 38, 255, 0.3); }
    }
    .subtitle {
        font-family: 'Courier New', monospace;
        color: #00f0ff;
        font-size: 1.2rem;
        letter-spacing: 8px;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        border-bottom: 1px solid rgba(0, 240, 255, 0.2);
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .css-1d391kg, .css-1633s9g {
        background: rgba(10, 10, 20, 0.95) !important;
        border-right: 1px solid rgba(0, 240, 255, 0.2) !important;
        backdrop-filter: blur(10px);
    }
    .css-1d391kg p, .css-1633s9g p,
    .css-1d391kg label, .css-1633s9g label,
    .css-1d391kg div, .css-1633s9g div,
    .css-1d391kg span, .css-1633s9g span {
        color: #ffffff !important;
        font-weight: 400 !important;
    }
    .recommendation-container {
        background: rgba(15, 15, 35, 0.85);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 12px;
        padding: 20px;
        margin: 15px 0;
        backdrop-filter: blur(10px);
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.05);
        transition: all 0.3s ease;
    }
    .recommendation-container:hover {
        border-color: #00f0ff;
        box-shadow: 0 0 40px rgba(0, 240, 255, 0.15);
        transform: translateY(-2px);
    }
    .recommendation-title {
        color: #00f0ff;
        font-family: 'Courier New', monospace;
        font-size: 1.2rem;
        font-weight: bold;
        letter-spacing: 2px;
        margin-bottom: 10px;
        text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
    }
    .recommendation-item {
        color: #ffffff;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        padding: 6px 0;
        border-bottom: 1px solid rgba(0, 240, 255, 0.05);
        line-height: 1.6;
    }
    .recommendation-item:last-child { border-bottom: none; }
    .recommendation-item .icon { margin-right: 8px; }
    .stButton > button {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(176, 38, 255, 0.15)) !important;
        border: 1px solid rgba(0, 240, 255, 0.4) !important;
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(5px);
        text-shadow: 0 0 10px rgba(0, 240, 255, 0.2);
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.3), rgba(176, 38, 255, 0.3)) !important;
        border-color: #00f0ff !important;
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.3) !important;
        transform: scale(1.02);
        color: #ffffff !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, rgba(0, 240, 255, 0.25), rgba(176, 38, 255, 0.25)) !important;
        border: 1px solid #00f0ff !important;
        box-shadow: 0 0 30px rgba(0, 240, 255, 0.2) !important;
        color: #ffffff !important;
    }
    [data-testid="metric-container"] {
        background: rgba(15, 15, 35, 0.8);
        border: 1px solid rgba(0, 240, 255, 0.15);
        border-radius: 10px;
        padding: 15px;
        backdrop-filter: blur(5px);
    }
    [data-testid="metric-container"] label {
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 2px;
        font-size: 0.8rem !important;
    }
    [data-testid="metric-container"] div {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
    }
    .dataframe {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.15) !important;
        border-radius: 10px !important;
        font-family: 'Courier New', monospace !important;
    }
    .dataframe th {
        color: #00f0ff !important;
        background: rgba(0, 240, 255, 0.1) !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
        font-size: 0.9rem !important;
    }
    .dataframe td {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.85rem !important;
    }
    .streamlit-expanderHeader {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.15) !important;
        border-radius: 8px !important;
        color: #00f0ff !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold !important;
    }
    .streamlit-expanderContent {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.1) !important;
        border-top: none !important;
    }
    .streamlit-expanderContent p, .streamlit-expanderContent div,
    .streamlit-expanderContent li, .streamlit-expanderContent span {
        color: #ffffff !important;
    }
    .stSelectbox [data-baseweb="select"] {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        color: #00f0ff !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
    }
    .stAlert {
        background: rgba(15, 15, 35, 0.9) !important;
        border: 1px solid rgba(0, 240, 255, 0.2) !important;
        border-radius: 8px !important;
    }
    .stAlert p, .stAlert div, .stAlert li, .stAlert span { color: #ffffff !important; }
    .stProgress > div > div {
        background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95) !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(15, 15, 35, 0.8) !important;
        border: 1px solid rgba(0, 240, 255, 0.15) !important;
        border-radius: 8px !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #a0a0c0 !important;
        font-family: 'Courier New', monospace !important;
        letter-spacing: 2px;
        text-transform: uppercase;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #00f0ff !important;
        border-bottom: 2px solid #00f0ff !important;
        font-weight: bold !important;
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: rgba(10, 10, 20, 0.5); }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #00f0ff, #b026ff);
        border-radius: 3px;
    }
    .folium-map {
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 12px;
        box-shadow: 0 0 40px rgba(0, 240, 255, 0.05);
    }
    .cyber-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #00f0ff, #b026ff, #ff2d95, transparent);
        margin: 20px 0;
        opacity: 0.5;
    }
    .stMarkdown p, .stMarkdown li {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        line-height: 1.6 !important;
    }
    .stMarkdown h1 { color: #00f0ff !important; }
    .stMarkdown h2 { color: #b026ff !important; }
    .stMarkdown h3 { color: #ff2d95 !important; }
    .stMarkdown h4 { color: #39ff14 !important; }
    .stCaption {
        color: #a0a0c0 !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.8rem !important;
    }
    .stRadio label {
        color: #ffffff !important;
        font-family: 'Courier New', monospace !important;
        font-size: 0.9rem !important;
    }
    .stRadio [role="radiogroup"] {
        gap: 8px;
    }
    @keyframes hazePulse {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 100, 0, 0.3); }
        50% { box-shadow: 0 0 40px rgba(255, 100, 0, 0.6); }
    }
    .haze-alert { animation: hazePulse 2s ease-in-out infinite; }
    @keyframes fogPulse {
        0%, 100% { box-shadow: 0 0 20px rgba(0, 240, 255, 0.3); }
        50% { box-shadow: 0 0 40px rgba(0, 240, 255, 0.6); }
    }
    .fog-alert { animation: fogPulse 2s ease-in-out infinite; }
</style>
"""

# ============================================================================
# PROTECTED DARK-SKY ZONES IN WEST MALAYSIA (v3.2.5 — tuned radii)
# ============================================================================

PROTECTED_DARK_SKY_ZONES = {
    'Taman Negara': (4.5000, 102.4000, 30, 'National Park',
                     '4,343 km² protected rainforest — Malaysia\'s oldest national park'),
    'Cameron Highlands': (4.4700, 101.3800, 12, 'Highland Station',
                          'Cool highland resort, elevation 1,500m'),
    'Genting Highlands': (3.4236, 101.7939, 8, 'Highland Resort',
                          'Highland resort at 1,740m, above the light dome'),
    'Fraser\'s Hill (Bukit Fraser)': (3.7167, 101.7333, 8, 'Hill Station',
                                       'Colonial hill station, elevation 1,500m'),
    'Bukit Tinggi': (3.3500, 101.8300, 6, 'Hill Resort',
                     'Highland retreat near Genting'),
    'Maxwell Hill (Bukit Larut)': (4.8600, 100.7500, 8, 'Hill Station',
                                    'Malaysia\'s wettest hill station, 1,000m'),
    'Penang Hill': (5.4200, 100.2700, 6, 'Hill Station',
                    'Historic hill station, 833m elevation'),
    'Gunung Jerai': (5.7800, 100.4300, 6, 'Mountain',
                     'Isolated mountain, 1,217m, coastal views'),
    'Bukit Hijau': (5.4000, 100.5500, 6, 'Recreational Forest',
                    'Remote forest reserve with dark skies'),
    'Royal Belum State Park': (5.5500, 101.4000, 25, 'State Park',
                                'Protected rainforest, remote wilderness'),
    'Endau-Rompin National Park': (2.5500, 103.3500, 25, 'National Park',
                                    'One of the oldest rainforests in the world'),
    'Gunung Ledang (Mount Ophir)': (2.3733, 102.6072, 8, 'National Park',
                                     'Famous mountain, 1,276m, legendary peak'),
    'Taman Negara Johor (Gunung Panti)': (1.8500, 103.7000, 10, 'State Park',
                                           'Remote forest reserve in Johor'),
    'Bukit Bintang Genting': (3.4500, 101.8000, 5, 'Reserve',
                              'Adjacent to Genting highlands'),
    'Gunung Nuang': (3.2300, 101.8700, 6, 'Forest Reserve',
                     '1,493m mountain, near Kuala Lumpur'),
    'Bukit Kutu': (3.5833, 101.7333, 6, 'Forest Reserve',
                   '1,053m hill, cool climate'),
    'Bukit Kledang': (4.6000, 101.0667, 5, 'Forest Reserve',
                      'Near Ipoh, elevated forest'),
    'Bukit Bendera (Penang)': (5.4200, 100.2700, 6, 'Hill Station',
                                'Penang Hill, 833m'),
}

# ============================================================================
# MANUAL ELEVATION OVERRIDES FOR CURATED CANDIDATES (v3.2.5)
# ============================================================================

CANDIDATE_ELEVATIONS = {
    'Cameron Highlands, Pahang': 1500,
    'Brinchang, Cameron Highlands': 1600,
    'Tanah Rata, Cameron Highlands': 1450,
    'Genting Highlands, Pahang': 1740,
    'Fraser\'s Hill (Bukit Fraser)': 1500,
    'Bukit Tinggi, Pahang': 750,
    'Maxwell Hill (Bukit Larut), Perak': 1000,
    'Gunung Jerai, Kedah': 1217,
    'Penang Hill, Penang': 833,
    'Taman Negara, Pahang': 150,
    'Kuala Tahan, Taman Negara': 100,
    'Royal Belum State Park, Perak': 300,
    'Endau-Rompin National Park, Johor': 250,
    'Gunung Ledang (Mount Ophir), Johor': 1276,
    'Pulau Tioman, Pahang': 100,
    'Pulau Redang, Terengganu': 50,
    'Pulau Perhentian, Terengganu': 50,
    'Pulau Kapas, Terengganu': 30,
    'Pulau Langkawi, Kedah': 100,
    'Pulau Pangkor, Perak': 30,
    'Desaru Coast, Johor': 20,
    'Mersing, Johor': 30,
    'Kukup, Johor': 20,
    'Tanjung Piai, Johor': 15,
    'Kuala Selangor, Selangor': 30,
    'Sekinchan, Selangor': 20,
    'Pantai Cahaya Negeri, N. Sembilan': 20,
    'Tanjung Tuan, N. Sembilan': 60,
    'Sungai Lembing, Pahang': 200,
    'Cherating, Pahang': 20,
    'Kuala Rompin, Pahang': 30,
    'Hulu Langat, Selangor': 200,
    'Batang Kali, Selangor': 200,
    'Bukit Kutu, Selangor': 1053,
    'Pulau Ketam, Selangor': 15,
    'Gua Musang, Kelantan': 150,
    'Kuala Berang, Terengganu': 100,
    'Jerantut, Pahang': 100,
    'Raub, Pahang': 150,
    'Kuala Lipis, Pahang': 200,
    'Gerik, Perak': 300,
    'Lenggong, Perak': 150,
    'Baling, Kedah': 200,
    'Sik, Kedah': 250,
    'Gunung Bintang, Kedah': 1862,
    'Pulau Sibu, Johor': 50,
    'Pulau Tinggi, Johor': 200,
    'Pulau Pemanggil, Johor': 150,
    'Pulau Aur, Johor': 100,
    'Pulau Besar, Melaka': 30,
    'Gunung Nuang': 1493,
    'Gunung Nuang (Forest Reserve)': 1493,
    'Ampang': 30,
    'Hulu Langat': 200,
    'Batang Kali': 200,
    'Bukit Kutu': 1053,
    'Selayang': 100,
    'Gombak': 150,
    'Rawang': 50,
}

PEAK_ELEVATIONS = {
    'gunung nuang': 1493,
    'gunung ledang': 1276,
    'gunung bintang': 1862,
    'gunung jerai': 1217,
    'gunung tahan': 2187,
    'gunung kinabalu': 4095,
    'gunung brinchang': 2032,
    'gunung irau': 2110,
    'gunung pulai': 654,
    'gunung panti': 531,
    'gunung kutu': 1053,
    'gunung besi': 833,
    'bukit kutu': 1053,
    'bukit larut': 1000,
    'bukit bendera': 833,
    'penang hill': 833,
}

# ============================================================================
# SEASONAL GUIDANCE (unchanged)
# ============================================================================

SEASONAL_GUIDANCE = {
    'Northwest Coast (Penang, Kedah, Perlis)': {
        'best_months': 'December - March',
        'good_months': 'April, November',
        'avoid_months': 'September - October (SW monsoon)',
        'notes': 'Dry season during NE monsoon. Clearer skies in early morning.'
    },
    'East Coast (Kelantan, Terengganu, Pahang)': {
        'best_months': 'February - May',
        'good_months': 'January, June',
        'avoid_months': 'November - January (NE monsoon)',
        'notes': 'Heavy rain during NE monsoon. Best during dry months Mar-May.'
    },
    'Central Highlands (Cameron, Genting, Fraser\'s Hill)': {
        'best_months': 'January - March, June - August',
        'good_months': 'April, May, September',
        'avoid_months': 'October - December (monsoon)',
        'notes': 'Cooler highland climate. Morning clearest before afternoon clouds.'
    },
    'West Coast (KL, Selangor, Melaka, Johor)': {
        'best_months': 'January - March, June - August',
        'good_months': 'April, May, September',
        'avoid_months': 'October - December (SW monsoon transition)',
        'notes': 'Two dry seasons. Best viewing during inter-monsoon periods.'
    },
    'Southern Johor (Johor Bahru, Endau-Rompin)': {
        'best_months': 'February - April, July - September',
        'good_months': 'January, May, June',
        'avoid_months': 'November - December (NE monsoon)',
        'notes': 'Equatorial climate. Best during drier months.'
    },
}

# ============================================================================
# HAZE SEASONAL CALENDAR (unchanged)
# ============================================================================

HAZE_SEASONAL_CALENDAR = {
    1:  ('Low', 'NE Monsoon rains', '20-50', 'Northeast monsoon brings rain, washes out haze. Clearest month.'),
    2:  ('Low', 'NE Monsoon', '25-60', 'Continued rain. Very low haze risk. Best for stargazing.'),
    3:  ('Low-Moderate', 'Transitional', '40-80', 'Transition period. Some dry days. Haze may start appearing.'),
    4:  ('Moderate', 'Local burning', '50-100', 'Hot season starts. Local burning possible. Monitor AQI.'),
    5:  ('Moderate', 'Local burning', '60-120', 'Dry season begins. Local fires possible in Pahang/Johor.'),
    6:  ('High', 'Sumatra fires', '80-200', 'SW monsoon begins. Smoke from Indonesian fires drifts over.'),
    7:  ('Very High', 'Sumatra fires', '100-250', 'PEAK HAZE SEASON. Transboundary smoke from Sumatra.'),
    8:  ('Very High', 'Sumatra fires', '120-300', 'PEAK HAZE SEASON. Worst air quality. Avoid stargazing.'),
    9:  ('Very High', 'Sumatra fires', '100-250', 'Continued heavy haze. Wait for rain.'),
    10: ('High', 'Sumatra fires fading', '80-200', 'Haze begins to decrease as monsoon returns.'),
    11: ('Moderate', 'Transitional', '50-120', 'NE monsoon returns. Rain washes haze away.'),
    12: ('Low', 'NE Monsoon', '30-70', 'Full monsoon. Clear skies, no haze. Great for stargazing.'),
}

# ============================================================================
# MOON PHASE CALCULATION (unchanged)
# ============================================================================

def calculate_moon_phase(date: datetime = None) -> Dict:
    """Calculate moon phase using a simplified astronomical algorithm."""
    if date is None:
        date = datetime.now()
    
    known_new_moon = datetime(2000, 1, 6, 18, 14, 0)
    synodic_month = 29.530588853
    
    days_since = (date - known_new_moon).total_seconds() / 86400.0
    phase_fraction = (days_since % synodic_month) / synodic_month
    age_days = phase_fraction * synodic_month
    
    illumination = (1 - math.cos(2 * math.pi * phase_fraction)) / 2
    illumination_pct = illumination * 100
    
    if phase_fraction < 0.03 or phase_fraction > 0.97:
        phase_name, emoji = "New Moon", "🌑"
    elif phase_fraction < 0.22:
        phase_name, emoji = "Waxing Crescent", "🌒"
    elif phase_fraction < 0.28:
        phase_name, emoji = "First Quarter", "🌓"
    elif phase_fraction < 0.47:
        phase_name, emoji = "Waxing Gibbous", "🌔"
    elif phase_fraction < 0.53:
        phase_name, emoji = "Full Moon", "🌕"
    elif phase_fraction < 0.72:
        phase_name, emoji = "Waning Gibbous", "🌖"
    elif phase_fraction < 0.78:
        phase_name, emoji = "Last Quarter", "🌗"
    else:
        phase_name, emoji = "Waning Crescent", "🌘"
    
    viewing_score = 5.0 - (illumination * 4.5)
    
    if illumination < 0.15:
        impact, impact_emoji = "Excellent - Dark skies for deep-sky objects", "🌟"
    elif illumination < 0.35:
        impact, impact_emoji = "Good - Faint deep-sky objects still visible", "✨"
    elif illumination < 0.60:
        impact, impact_emoji = "Moderate - Brighter objects visible, faint ones washed out", "⭐"
    elif illumination < 0.85:
        impact, impact_emoji = "Poor - Only brightest objects visible", "⚠️"
    else:
        impact, impact_emoji = "Very Poor - Moon washes out most stars", "❌"
    
    return {
        'phase_name': phase_name,
        'emoji': emoji,
        'illumination_pct': round(illumination_pct, 1),
        'age_days': round(age_days, 1),
        'viewing_score': round(viewing_score, 2),
        'impact': impact,
        'impact_emoji': impact_emoji,
        'date': date.strftime('%Y-%m-%d %H:%M'),
    }


# ============================================================================
# MILKY WAY VISIBILITY CALENDAR (unchanged)
# ============================================================================

def get_milky_way_visibility(lat: float, lon: float, date: datetime = None) -> Dict:
    """Determine if the Milky Way galactic core is visible."""
    if date is None:
        date = datetime.now()
    
    month = date.month
    
    if month in [3, 4, 5]:
        visibility = "Excellent"
        best_time = "2:00 AM - 5:00 AM"
        score = 5.0
        note = "Galactic core rises around 2 AM. Best months for viewing the core!"
    elif month in [6, 7, 8]:
        visibility = "Peak"
        best_time = "10:00 PM - 4:00 AM"
        score = 5.0
        note = "PEAK SEASON! Galactic core visible all night. Best viewing of the year."
    elif month in [9, 10]:
        visibility = "Good"
        best_time = "8:00 PM - 12:00 AM"
        score = 4.0
        note = "Core visible in early evening. Still great viewing."
    elif month in [2, 11]:
        visibility = "Limited"
        best_time = "3:00 AM - 5:00 AM"
        score = 2.5
        note = "Core barely above horizon. Outer arms only."
    else:
        visibility = "Poor"
        best_time = "Not visible"
        score = 1.0
        note = "Galactic core below horizon. Only outer Milky Way arms visible."
    
    abs_lat = abs(lat)
    if abs_lat < 3:
        lat_bonus = "Perfect - Directly overhead at zenith"
    elif abs_lat < 5:
        lat_bonus = "Excellent - High in the sky"
    elif abs_lat < 7:
        lat_bonus = "Good - Well positioned"
    else:
        lat_bonus = "Moderate - Lower in sky"
    
    if month in [1, 2, 11, 12]:
        next_window = "March - October (best: June - August)"
    else:
        next_window = "Currently in season!"
    
    return {
        'visibility': visibility,
        'best_time': best_time,
        'score': score,
        'note': note,
        'latitude_note': lat_bonus,
        'next_window': next_window,
        'month': month,
    }


# ============================================================================
# ASTROPHOTOGRAPHY SCORE (unchanged)
# ============================================================================

def calculate_astrophotography_scores(result_data: Dict, moon_phase: Dict) -> Dict:
    """Calculate separate scores for naked-eye, telescope, and astrophotography."""
    base_score = result_data.get('suitability_percentage', 0)
    elevation_m = result_data.get('elevation_m', 0)
    lp_index = result_data.get('light_pollution_index', 0)
    humidity = result_data.get('humidity_pct')
    visibility_km = result_data.get('visibility_km')
    protected = result_data.get('protected_zone')
    moon_illum = moon_phase.get('illumination_pct', 50)
    haze_data = result_data.get('haze', {})
    haze_severity = haze_data.get('severity', 'None')
    haze_detected = haze_data.get('detected', False)
    
    is_smoke_haze = haze_detected and haze_severity not in ['Fog', 'None']
    
    naked_eye = base_score
    naked_eye -= (moon_illum / 100.0) * 25
    if lp_index >= 5:
        naked_eye -= 10
    if protected:
        naked_eye += 5
    if is_smoke_haze:
        if haze_severity == 'Heavy':
            naked_eye -= 20
        elif haze_severity == 'Moderate':
            naked_eye -= 10
        elif haze_severity == 'Light':
            naked_eye -= 5
    naked_eye = max(0, min(100, naked_eye))
    
    telescope = base_score
    telescope -= (moon_illum / 100.0) * 12
    if elevation_m > 1000:
        telescope += 8
    elif elevation_m > 500:
        telescope += 4
    if humidity and humidity > 85:
        telescope -= 8
    elif humidity and humidity > 70:
        telescope -= 3
    if is_smoke_haze:
        if haze_severity == 'Heavy':
            telescope -= 18
        elif haze_severity == 'Moderate':
            telescope -= 9
        elif haze_severity == 'Light':
            telescope -= 4
    telescope = max(0, min(100, telescope))
    
    astro = base_score
    astro -= (moon_illum / 100.0) * 30
    if lp_index >= 8:
        astro -= 25
    elif lp_index >= 5:
        astro -= 12
    elif lp_index <= 1:
        astro += 8
    if visibility_km and visibility_km < 10:
        astro -= 10
    elif visibility_km and visibility_km > 25:
        astro += 5
    if humidity and humidity > 90:
        astro -= 12
    elif humidity and humidity > 80:
        astro -= 5
    if protected:
        astro += 10
    if elevation_m > 1000:
        astro += 8
    if is_smoke_haze:
        if haze_severity == 'Heavy':
            astro -= 30
        elif haze_severity == 'Moderate':
            astro -= 15
        elif haze_severity == 'Light':
            astro -= 6
    astro = max(0, min(100, astro))
    
    def rate(score):
        if score >= 80:
            return "Excellent", "🌟"
        elif score >= 65:
            return "Good", "✨"
        elif score >= 50:
            return "Moderate", "⭐"
        elif score >= 35:
            return "Limited", "⚠️"
        else:
            return "Poor", "❌"
    
    naked_rating, naked_emoji = rate(naked_eye)
    telescope_rating, telescope_emoji = rate(telescope)
    astro_rating, astro_emoji = rate(astro)
    
    return {
        'naked_eye': {
            'score': round(naked_eye, 1),
            'rating': naked_rating,
            'emoji': naked_emoji,
            'note': 'Best for casual viewing, Milky Way, constellations'
        },
        'telescope': {
            'score': round(telescope, 1),
            'rating': telescope_rating,
            'emoji': telescope_emoji,
            'note': 'Best for planets, clusters, nebulae'
        },
        'astrophotography': {
            'score': round(astro, 1),
            'rating': astro_rating,
            'emoji': astro_emoji,
            'note': 'Best for long-exposure deep-sky imaging'
        },
    }


# ============================================================================
# HAZE DETECTION ENGINE (v3.2.5 — refined)
# ============================================================================

def detect_haze(weather_data: Optional[Dict], air_quality: Optional[Dict], 
                location: Dict, date: datetime = None) -> Dict:
    """Detect transboundary smoke haze OR natural fog (temperate or tropical)."""
    if date is None:
        date = datetime.now()
    
    month = date.month
    seasonal = HAZE_SEASONAL_CALENDAR.get(month, HAZE_SEASONAL_CALENDAR[6])
    seasonal_risk, seasonal_source, seasonal_aqi, seasonal_note = seasonal
    
    result = {
        'detected': False,
        'severity': 'None',
        'confidence': 'Low',
        'indicators': [],
        'cause': 'Unknown',
        'aqi': None,
        'aqi_category': None,
        'pm25': None,
        'pm10': None,
        'seasonal_risk': seasonal_risk,
        'seasonal_source': seasonal_source,
        'seasonal_note': seasonal_note,
        'seasonal_aqi_range': seasonal_aqi,
        'month': month,
        'health_advisory': None,
        'action_recommendation': None,
        'pm25_level': None,
        'is_fog': False,
        'fog_type': None,
        # v3.2.6: cross-check info
        'waqi_pm25': None,
        'waqi_aqi': None,
        'waqi_station': None,
        'waqi_station_distance_km': None,
        'ground_verified': False,
        'source_label': 'Open-Meteo Air Quality (Live)',
    }
    
    pm25 = None
    pm10 = None
    aqi = None    
    if air_quality:
        pm25 = air_quality.get('pm2_5')
        pm10 = air_quality.get('pm10')
        aqi = air_quality.get('us_aqi') or air_quality.get('european_aqi')
        
        result['pm25'] = pm25
        result['pm10'] = pm10
        result['aqi'] = aqi
        result['source_label'] = air_quality.get('source', 'Open-Meteo Air Quality (Live)')
        
        # Capture WAQI cross-check data if present (validated by distance)
        if air_quality.get('waqi_pm25') is not None:
            result['waqi_pm25'] = air_quality.get('waqi_pm25')
            result['waqi_aqi'] = air_quality.get('waqi_aqi')
            result['waqi_station'] = air_quality.get('waqi_station')
            result['waqi_station_distance_km'] = air_quality.get('waqi_station_distance_km')
            result['ground_verified'] = True
        
        if pm25 is not None:
            if pm25 < 12:
                result['pm25_level'] = 'Good'
                result['indicators'].append(f"PM2.5: {pm25:.1f} µg/m³ (Good)")
            elif pm25 < 35:
                result['pm25_level'] = 'Moderate'
                result['indicators'].append(f"PM2.5: {pm25:.1f} µg/m³ (Moderate)")
            elif pm25 < 55:
                result['pm25_level'] = 'Unhealthy for Sensitive'
                result['indicators'].append(f"PM2.5: {pm25:.1f} µg/m³ (Unhealthy for sensitive groups)")
            elif pm25 < 150:
                result['pm25_level'] = 'Unhealthy'
                result['indicators'].append(f"PM2.5: {pm25:.1f} µg/m³ (UNHEALTHY)")
            elif pm25 < 250:
                result['pm25_level'] = 'Very Unhealthy'
                result['indicators'].append(f"PM2.5: {pm25:.1f} µg/m³ (VERY UNHEALTHY)")
            else:
                result['pm25_level'] = 'Hazardous'
                result['indicators'].append(f"PM2.5: {pm25:.1f} µg/m³ (HAZARDOUS)")
        
        if aqi is not None:
            if aqi <= 50:
                result['aqi_category'] = 'Good'
            elif aqi <= 100:
                result['aqi_category'] = 'Moderate'
            elif aqi <= 150:
                result['aqi_category'] = 'Unhealthy for Sensitive'
            elif aqi <= 200:
                result['aqi_category'] = 'Unhealthy'
            elif aqi <= 300:
                result['aqi_category'] = 'Very Unhealthy'
            else:
                result['aqi_category'] = 'Hazardous'
    
    visibility = None
    if weather_data:
        visibility = weather_data.get('visibility_km')
        if visibility is not None:
            if visibility < 2:
                result['indicators'].append(f"Visibility: {visibility:.1f} km (VERY LOW - heavy haze/fog)")
            elif visibility < 5:
                result['indicators'].append(f"Visibility: {visibility:.1f} km (LOW - likely haze/fog)")
            elif visibility < 10:
                result['indicators'].append(f"Visibility: {visibility:.1f} km (reduced)")
            else:
                result['indicators'].append(f"Visibility: {visibility:.1f} km (normal)")
    
    humidity = None
    if weather_data:
        humidity = weather_data.get('humidity_pct')
        if humidity is not None and humidity > 85:
            result['indicators'].append(f"Humidity: {humidity:.0f}% (high - supports haze/fog formation)")
    
    temperature = None
    if weather_data:
        temperature = weather_data.get('temperature_c')
    
    cloud_cover = None
    if weather_data:
        cloud_cover = weather_data.get('cloud_cover_pct')
        if cloud_cover is not None and cloud_cover > 80:
            result['indicators'].append(f"Cloud/smoke cover: {cloud_cover:.0f}%")
    
    if seasonal_risk in ['High', 'Very High']:
        result['indicators'].append(f"Season: {seasonal_risk} haze risk ({seasonal_source})")
    
    # FOG CHECK
    elevation_m = location.get('elevation_m', 0)
    is_high_altitude = elevation_m > 1000
    is_low_visibility = visibility is not None and visibility < 5
    is_clean_air = pm25 is None or pm25 < 35
    is_cold = temperature is not None and temperature < 10
    is_humid = humidity is not None and humidity > 90
    is_fog_condition = is_cold or is_humid
    
    if is_high_altitude and is_low_visibility and is_clean_air and is_fog_condition:
        if is_cold:
            fog_type = 'temperate'
            temp_note = f"{temperature:.1f}°C — cold mountain climate"
        else:
            fog_type = 'tropical'
            temp_note = f"{temperature:.1f}°C, {humidity:.0f}% humidity — tropical highland"
        
        result['detected'] = True
        result['severity'] = 'Fog'
        result['confidence'] = 'High'
        result['is_fog'] = True
        result['fog_type'] = fog_type
        result['cause'] = f'Natural mountain fog ({fog_type} highland at {elevation_m:.0f}m, {temp_note})'
        result['indicators'].append(f"🌫️ Natural mountain fog detected (not smoke)")
        result['health_advisory'] = (
            "✅ Air quality is CLEAN. This is natural mountain fog — not smoke. "
            "Safe for outdoor activity (but cool and damp — bring a jacket!)."
        )
        result['action_recommendation'] = (
            f"☁️ Location is inside a natural cloud (visibility {visibility:.1f} km). "
            f"Try again in 1-2 hours — highland fog often clears by morning. "
            f"Move to lower elevation for clearer views if needed."
        )
        return result
    
    # STANDARD HAZE DETECTION
    severity_score = 0
    
    if pm25 is not None:
        if pm25 >= 150:
            severity_score += 5
        elif pm25 >= 55:
            severity_score += 3
        elif pm25 >= 35:
            severity_score += 2
        elif pm25 >= 12:
            severity_score += 1
    
    if aqi is not None:
        if aqi >= 200:
            severity_score += 5
        elif aqi >= 150:
            severity_score += 3
        elif aqi >= 100:
            severity_score += 2
        elif aqi >= 50:
            severity_score += 1
    
    if visibility is not None:
        if visibility < 2:
            severity_score += 4
        elif visibility < 5:
            severity_score += 3
        elif visibility < 10:
            severity_score += 1
    
    if humidity is not None and humidity > 90 and visibility is not None and visibility < 10:
        severity_score += 2
    
    if seasonal_risk in ['High', 'Very High']:
        severity_score += 1
    
    if severity_score >= 10:
        result['severity'] = 'Severe'
        result['confidence'] = 'Very High'
        result['detected'] = True
    elif severity_score >= 7:
        result['severity'] = 'Heavy'
        result['confidence'] = 'High'
        result['detected'] = True
    elif severity_score >= 4:
        result['severity'] = 'Moderate'
        result['confidence'] = 'Medium'
        result['detected'] = True
    elif severity_score >= 2:
        result['severity'] = 'Light'
        result['confidence'] = 'Medium'
        result['detected'] = True
    else:
        result['severity'] = 'None'
        result['confidence'] = 'Low'
        result['detected'] = False
    
    if month in [6, 7, 8, 9, 10] and result['detected']:
        result['cause'] = 'Transboundary smoke haze (Sumatra fires - SW monsoon season)'
    elif result['detected']:
        result['cause'] = 'Local burning or regional smoke'
    else:
        result['cause'] = 'No significant haze detected'
    
    if result['severity'] in ['Heavy', 'Severe']:
        result['health_advisory'] = (
            "⚠️ HEALTH ADVISORY: Air quality is unhealthy. "
            "Wear N95 mask if going outdoors. Sensitive groups (children, elderly, "
            "respiratory issues) should stay indoors. Avoid outdoor exercise."
        )
    elif result['severity'] == 'Moderate':
        result['health_advisory'] = (
            "💛 Health Note: Air quality is degraded. "
            "Sensitive groups should limit outdoor activity. "
            "Consider wearing a mask outdoors."
        )
    elif result['severity'] == 'Light':
        result['health_advisory'] = (
            "💚 Minor: Slight haze. Sensitive individuals may notice reduced air quality. "
            "Fine for most outdoor activities."
        )
    else:
        result['health_advisory'] = "✅ Air quality is good. Safe for all outdoor activities."
    
    if result['severity'] in ['Heavy', 'Severe']:
        result['action_recommendation'] = (
            "🚫 NOT RECOMMENDED for stargazing tonight. Wait for rain to wash out haze, "
            "or choose a coastal site with sea breeze (better dispersion). "
            "Check back in 2-3 days after rainfall."
        )
    elif result['severity'] == 'Moderate':
        result['action_recommendation'] = (
            "⚠️ Marginal conditions. Haze will reduce visibility of faint objects. "
            "Only brightest stars/planets visible. Consider postponing for clearer night."
        )
    elif result['severity'] == 'Light':
        result['action_recommendation'] = (
            "✅ Acceptable conditions. Slight haze reduces contrast but viewing is possible. "
            "Best for bright objects (Moon, planets, bright stars)."
        )
    else:
        result['action_recommendation'] = (
            "🌟 Excellent air quality. Perfect for all types of stargazing."
        )
    
    return result


def get_air_quality(location: Dict) -> Optional[Dict]:
    """Fetch live air quality data from Open-Meteo Air Quality API."""
    try:
        url = "https://air-quality-api.open-meteo.com/v1/air-quality"
        params = {
            "latitude": location['lat'],
            "longitude": location['lon'],
            "current": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
                       "sulphur_dioxide,ozone,aerosol_optical_depth,"
                       "dust,uv_index,us_aqi,european_aqi",
            "timezone": "auto",
        }
        r = requests.get(url, params=params, timeout=5)
        data = r.json()
        cur = data.get("current", {})
        return {
            'pm2_5': cur.get('pm2_5'),
            'pm10': cur.get('pm10'),
            'carbon_monoxide': cur.get('carbon_monoxide'),
            'nitrogen_dioxide': cur.get('nitrogen_dioxide'),
            'sulphur_dioxide': cur.get('sulphur_dioxide'),
            'ozone': cur.get('ozone'),
            'aerosol_optical_depth': cur.get('aerosol_optical_depth'),
            'dust': cur.get('dust'),
            'uv_index': cur.get('uv_index'),
            'us_aqi': cur.get('us_aqi'),
            'european_aqi': cur.get('european_aqi'),
            'source': 'Open-Meteo Air Quality (Live)',
            'time': cur.get('time'),
        }
    except Exception:
        return None


def get_waqi_air_quality(location: Dict) -> Optional[Dict]:
    """
    V3.2.7: WAQI (aqicn.org) ground-station lookup with STRICT distance
    validation. The public 'demo' token is shared globally and can return
    stations far away (e.g. Shanghai for a Malaysian query). We reject any
    station >100 km from the requested coordinates.

    Returns None if unavailable or too far.
    """
    try:
        url = f"https://api.waqi.info/feed/geo:{location['lat']};{location['lon']}/?token=demo"
        r = requests.get(url, timeout=4)
        data = r.json()
        if data.get('status') != 'ok':
            return None
        d = data.get('data', {})
        iaqi = d.get('iaqi', {})
        pm25_val = iaqi.get('pm25', {}).get('v')
        pm10_val = iaqi.get('pm10', {}).get('v')
        aqi_val = d.get('aqi')
        station = d.get('city', {}).get('name', 'Unknown')

        # V3.2.7: Distance validation — get station coordinates
        station_geo = d.get('city', {}).get('geo')
        if station_geo and len(station_geo) == 2:
            st_lat, st_lon = station_geo[0], station_geo[1]
            # Haversine distance
            R = 6371
            dlat = math.radians(st_lat - location['lat'])
            dlon = math.radians(st_lon - location['lon'])
            a = math.sin(dlat/2)**2 + \
                math.cos(math.radians(location['lat'])) * \
                math.cos(math.radians(st_lat)) * \
                math.sin(dlon/2)**2
            dist_km = R * 2 * math.asin(min(1, math.sqrt(a)))

            if dist_km > 100:
                # Station too far — reject
                return None
        else:
            # No coordinates from WAQI — reject to be safe
            # (Cannot verify the station is nearby)
            return None

        # Ignore if we got nothing useful
        if pm25_val is None and aqi_val is None:
            return None

        return {
            'pm2_5': pm25_val,
            'pm10': pm10_val,
            'us_aqi': aqi_val,
            'station': station,
            'station_distance_km': round(dist_km, 1),
            'source': 'WAQI (aqicn.org — DOE ground station)',
        }
    except Exception:
        return None


def get_merged_air_quality(location: Dict) -> Optional[Dict]:
    """
    V3.2.7: Merge Open-Meteo CAMS + WAQI ground station (with distance check).
    Takes the HIGHER PM2.5 value (conservative) — but only if WAQI station
    is within 100 km of the query point.

    Returns a dict with both individual values preserved plus a merged
    'pm2_5' that reflects the more conservative estimate.
    """
    openmeteo = get_air_quality(location)
    waqi = get_waqi_air_quality(location)  # already validated by distance

    if openmeteo is None and waqi is None:
        return None

    if openmeteo is None:
        # Only WAQI available
        return {
            'pm2_5': waqi.get('pm2_5'),
            'pm10': waqi.get('pm10'),
            'us_aqi': waqi.get('us_aqi'),
            'european_aqi': None,
            'carbon_monoxide': None,
            'nitrogen_dioxide': None,
            'sulphur_dioxide': None,
            'ozone': None,
            'aerosol_optical_depth': None,
            'dust': None,
            'uv_index': None,
            'waqi_pm25': waqi.get('pm2_5'),
            'waqi_pm10': waqi.get('pm10'),
            'waqi_aqi': waqi.get('us_aqi'),
            'waqi_station': waqi.get('station'),
            'waqi_station_distance_km': waqi.get('station_distance_km'),
            'openmeteo_pm25': None,
            'openmeteo_aqi': None,
            'source': 'WAQI ground station only',
            'time': None,
        }

    if waqi is None:
        # Only Open-Meteo available (WAQI was rejected or unavailable)
        openmeteo['waqi_pm25'] = None
        openmeteo['waqi_pm10'] = None
        openmeteo['waqi_aqi'] = None
        openmeteo['waqi_station'] = None
        openmeteo['waqi_station_distance_km'] = None
        openmeteo['openmeteo_pm25'] = openmeteo.get('pm2_5')
        openmeteo['openmeteo_aqi'] = openmeteo.get('us_aqi')
        openmeteo['source'] = 'Open-Meteo Air Quality (Live)'
        return openmeteo

    # Both available — apply "take higher PM2.5" rule
    om_pm25 = openmeteo.get('pm2_5')
    waqi_pm25 = waqi.get('pm2_5')

    om_aqi = openmeteo.get('us_aqi')
    waqi_aqi = waqi.get('us_aqi')

    merged_pm25 = None
    if om_pm25 is not None and waqi_pm25 is not None:
        merged_pm25 = max(om_pm25, waqi_pm25)
    elif waqi_pm25 is not None:
        merged_pm25 = waqi_pm25
    elif om_pm25 is not None:
        merged_pm25 = om_pm25

    merged_aqi = None
    if om_aqi is not None and waqi_aqi is not None:
        merged_aqi = max(om_aqi, waqi_aqi)
    elif waqi_aqi is not None:
        merged_aqi = waqi_aqi
    elif om_aqi is not None:
        merged_aqi = om_aqi

    # Preserve everything from Open-Meteo, then override key values
    result = dict(openmeteo)
    result['pm2_5'] = merged_pm25
    result['us_aqi'] = merged_aqi
    # If WAQI PM10 is higher, take it too (conservative)
    om_pm10 = openmeteo.get('pm10')
    waqi_pm10 = waqi.get('pm10')
    if om_pm10 is not None and waqi_pm10 is not None:
        result['pm10'] = max(om_pm10, waqi_pm10)
    elif waqi_pm10 is not None:
        result['pm10'] = waqi_pm10

    # Attach both sources + distance info for transparency
    result['waqi_pm25'] = waqi_pm25
    result['waqi_pm10'] = waqi_pm10
    result['waqi_aqi'] = waqi_aqi
    result['waqi_station'] = waqi.get('station')
    result['waqi_station_distance_km'] = waqi.get('station_distance_km')
    result['openmeteo_pm25'] = om_pm25
    result['openmeteo_aqi'] = om_aqi

    # Label — highlight that both were used
    result['source'] = 'Open-Meteo CAMS + WAQI ground station'

    return result


# ============================================================================
# RECOMMENDATION ENGINE (unchanged)
# ============================================================================

def get_seasonal_guidance(lat: float, lon: float, elevation_m: float) -> Dict:
    if lat > 5.0 and lon < 101.0:
        region = 'Northwest Coast (Penang, Kedah, Perlis)'
    elif lon > 102.5:
        region = 'East Coast (Kelantan, Terengganu, Pahang)'
    elif elevation_m > 800:
        region = 'Central Highlands (Cameron, Genting, Fraser\'s Hill)'
    elif lat < 3.0:
        region = 'Southern Johor (Johor Bahru, Endau-Rompin)'
    else:
        region = 'West Coast (KL, Selangor, Melaka, Johor)'
    
    guidance = SEASONAL_GUIDANCE.get(region, SEASONAL_GUIDANCE['West Coast (KL, Selangor, Melaka, Johor)'])
    return {'region': region, **guidance}


def generate_recommendation_strategy(result_data: Dict) -> Dict:
    score = result_data.get('suitability_percentage', 0)
    details = result_data.get('details', {})
    elevation_m = result_data.get('elevation_m', 0)
    cloud_risk = result_data.get('cloud_risk', 'Unknown')
    light_pollution = result_data.get('light_pollution_index', 0)
    cloud_cover = result_data.get('cloud_cover_pct', None)
    humidity = result_data.get('humidity_pct', None)
    protected_zone = result_data.get('protected_zone', None)
    lat_deg = result_data.get('lat_deg', 0)
    haze = result_data.get('haze', {})

    recommendations = {
        'immediate_actions': [],
        'short_term_actions': [],
        'long_term_actions': [],
        'investment_required': 'Low',
        'overall_feasibility': 'High',
        'risk_level': 'Low',
    }

    def add_action(bucket, text, priority, cost):
        recommendations[bucket].append({
            'text': text, 'priority': priority, 'cost': cost
        })

    haze_severity = haze.get('severity', 'None')
    is_fog = haze.get('is_fog', False)
    fog_type = haze.get('fog_type', None)
    
    if is_fog:
        if fog_type == 'tropical':
            fog_note = "Tropical highland fog (warm & humid, common at Cameron/Genting)"
        else:
            fog_note = "Cold mountain fog"
        add_action('short_term_actions',
            f'🌫️ {fog_note} ({haze.get("cause", "High-altitude cloud")}). '
            f'Not smoke — air is clean. Go to lower elevation for clearer views.',
            'Medium', '💸')
    elif haze_severity in ['Heavy', 'Severe']:
        add_action('immediate_actions',
            f'🌫️ HAZE ALERT ({haze_severity}): {haze.get("cause", "Smoke haze detected")}. Stargazing severely impacted.',
            'Critical', '💸')
    elif haze_severity == 'Moderate':
        add_action('short_term_actions',
            f'🌫️ Moderate haze detected. Visibility reduced. Check Air Quality Index before heading out.',
            'High', '💸')
    elif haze_severity == 'Light':
        add_action('short_term_actions',
            f'💨 Light haze. Minor impact on viewing. Best for bright objects.',
            'Medium', '💸')

    if protected_zone:
        inside = protected_zone.get('is_inside', True)
        tag = '🏞️ PROTECTED DARK-SKY ZONE' if inside else '🏞️ NEAR PROTECTED ZONE'
        add_action('immediate_actions',
            f'{tag}: {"" if inside else "Nearby "}"{protected_zone["name"]}" ({protected_zone["designation"]}, ~{protected_zone.get("distance_km", 0):.1f} km). {protected_zone["description"]}.',
            'Low', '💸')

    if elevation_m < 20:
        add_action('short_term_actions',
            '⛰️ Low elevation (<20m). More atmosphere to look through. Consider portable telescope platforms.',
            'Medium', '💸💸')
    elif elevation_m < 100:
        add_action('short_term_actions',
            '🌄 Moderate elevation. Good for general stargazing. Standard observation deck recommended.',
            'Low', '💸')
    elif elevation_m < 500:
        add_action('immediate_actions',
            '✅ EXCELLENT ELEVATION (100-500m). Less atmospheric distortion. Ideal for telescope installation.',
            'Low', '💸')
    elif elevation_m < 1000:
        add_action('immediate_actions',
            '🌟 OUTSTANDING ELEVATION (500-1000m). Thin atmosphere, superb seeing conditions. Prime location!',
            'Low', '💸💸')
    else:
        add_action('immediate_actions',
            f'🏔️ EXCEPTIONAL HIGH-ALTITUDE SITE ({elevation_m:.0f}m). World-class observatory potential. Very thin atmosphere — likely ABOVE the light dome.',
            'Low', '💸💸💸')
        recommendations['investment_required'] = 'Moderate'

    if light_pollution >= 8 and not protected_zone:
        add_action('immediate_actions',
            '🚨 CRITICAL: HIGH LIGHT POLLUTION. Need light shields or relocate to darker site.',
            'Critical', '💸💸💸💸')
        recommendations['investment_required'] = 'Very High'
    elif light_pollution >= 5 and not protected_zone:
        add_action('short_term_actions',
            '💡 MODERATE LIGHT POLLUTION. Install light barriers and coordinate with local authorities for dark-sky lighting.',
            'High', '💸💸💸')
        if recommendations['investment_required'] != 'Very High':
            recommendations['investment_required'] = 'Moderate'
    else:
        add_action('immediate_actions',
            '✅ DARK-SKY CONDITIONS. Excellent for galaxy viewing and deep-sky photography.',
            'Low', '💸')

    if cloud_risk == 'High' and not protected_zone:
        add_action('short_term_actions',
            '☁️ HIGH SEASONAL CLOUD RISK. Plan for flexible viewing schedules and indoor planetarium backup.',
            'High', '💸💸💸')
        if recommendations['investment_required'] != 'Very High':
            recommendations['investment_required'] = 'Moderate'
    elif cloud_risk == 'Low':
        add_action('immediate_actions',
            '✅ LOW CLOUD RISK. Excellent year-round viewing potential.',
            'Low', '💸')

    if lat_deg < 3:
        add_action('immediate_actions',
            f'🌌 EXCELLENT LATITUDE ({lat_deg:.1f}°N). Near equator — can view BOTH Northern AND Southern sky objects!',
            'Low', '💸')
    elif lat_deg < 5:
        add_action('immediate_actions',
            f'🌌 GOOD LATITUDE ({lat_deg:.1f}°N). Excellent access to Milky Way core and Magellanic Clouds.',
            'Low', '💸')
    else:
        add_action('short_term_actions',
            f'🌌 MODERATE LATITUDE ({lat_deg:.1f}°N). Still good viewing. Milky Way visible seasonally.',
            'Low', '💸')

    if cloud_cover is not None:
        if cloud_cover > 70:
            add_action('short_term_actions',
                f'☁️ HIGH CURRENT CLOUD COVER ({cloud_cover:.0f}%). Not the best night right now. Check seasonal guidance below.',
                'Medium', '💸')
        elif cloud_cover < 20:
            add_action('immediate_actions',
                f'✅ EXCELLENT CLEAR SKIES NOW ({cloud_cover:.0f}% cloud cover). Ideal viewing conditions tonight!',
                'Low', '💸')

    if humidity is not None and humidity > 85:
        add_action('short_term_actions',
            f'💧 HIGH HUMIDITY ({humidity:.0f}%). Install dew heaters for telescopes. Consider dehumidified storage.',
            'Medium', '💸💸')

    infra_details = details.get('infrastructure_access', {}).get('value', {})
    if isinstance(infra_details, dict):
        if infra_details.get('airports', 0) == 0:
            add_action('long_term_actions',
                '✈️ No airport nearby. Consider helipad for equipment delivery and visitor access.',
                'Medium', '💸💸💸')
        if infra_details.get('major_roads', 0) == 0:
            add_action('short_term_actions',
                '🛣️ Limited road access. Improve access roads for telescope equipment and visitors.',
                'High', '💸💸💸')
        if infra_details.get('accommodation', 0) == 0 and not protected_zone:
            add_action('long_term_actions',
                '🏨 No accommodation nearby. Build eco-lodge or observatory guest facilities.',
                'Medium', '💸💸💸💸')

    critical_count = sum(
        1 for a in recommendations['immediate_actions']
        if a['priority'] == 'Critical'
    )
    high_count = sum(
        1 for a in recommendations['short_term_actions']
        if a['priority'] == 'High'
    )

    if score >= 80:
        score_band, score_emoji = 'Excellent', '🌟'
    elif score >= 65:
        score_band, score_emoji = 'Good', '✨'
    elif score >= 50:
        score_band, score_emoji = 'Moderate', '⭐'
    elif score >= 35:
        score_band, score_emoji = 'Limited', '⚠️'
    else:
        score_band, score_emoji = 'Poor', '❌'

    if critical_count >= 3:
        feasibility = '❌ Poor - Major critical issues must be resolved before development'
        risk_level = 'Very High'
    elif critical_count == 2:
        feasibility = '⚠️ Limited - Multiple critical issues require resolution'
        risk_level = 'High'
    elif critical_count == 1:
        feasibility = '⭐ Moderate - One critical issue requires resolution'
        risk_level = 'High'
    elif high_count >= 2:
        feasibility = '⭐ Moderate - Several high-priority preparations required'
        risk_level = 'Medium'
    else:
        feasibility = f'{score_emoji} {score_band} - ' + {
            'Excellent': 'World-class stargazing destination potential',
            'Good': 'Excellent viewing site with minor improvements',
            'Moderate': 'Good viewing site requiring some investment',
            'Limited': 'Challenging conditions, major investment needed',
            'Poor': 'Not recommended for astronomy development',
        }[score_band]
        risk_level = {
            'Excellent': 'Low', 'Good': 'Low',
            'Moderate': 'Medium', 'Limited': 'High', 'Poor': 'Very High',
        }[score_band]

    recommendations['overall_feasibility'] = feasibility
    recommendations['risk_level'] = risk_level
    recommendations['critical_action_count'] = critical_count
    recommendations['high_action_count'] = high_count
    recommendations['total_action_count'] = len(
        recommendations['immediate_actions']
        + recommendations['short_term_actions']
        + recommendations['long_term_actions']
    )

    recommendations['timeline_summary'] = {
        'immediate': f"{len(recommendations['immediate_actions'])} actions (0-6 months)",
        'short_term': f"{len(recommendations['short_term_actions'])} actions (6-18 months)",
        'long_term': f"{len(recommendations['long_term_actions'])} actions (18-36 months)"
    }
    return recommendations


# ============================================================================
# CACHE MANAGEMENT (unchanged)
# ============================================================================

class APICache:
    def __init__(self, cache_dir: str = "starview_cache", ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _get_cache_key(self, url: str, params: Dict) -> str:
        key_str = url + json.dumps(params, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, url: str, params: Dict) -> Optional[Dict]:
        cache_key = self._get_cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            modified_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - modified_time < self.ttl:
                try:
                    with open(cache_file, 'r') as f:
                        return json.load(f)
                except Exception:
                    return None
        return None

    def set(self, url: str, params: Dict, data: Dict) -> None:
        cache_key = self._get_cache_key(url, params)
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception:
            pass

    def clear(self):
        for f in self.cache_dir.glob("*.json"):
            f.unlink()

    def get_stats(self) -> Dict:
        files = list(self.cache_dir.glob("*.json"))
        return {'total_cached': len(files), 'cache_dir': str(self.cache_dir)}

api_cache = APICache()

# ============================================================================
# WEST MALAYSIA LOCATIONS (all state dicts — unchanged)
# ============================================================================

PERLIS_LOCATIONS = {
    'Kangar': (6.4414, 100.1986),
    'Arau': (6.4294, 100.2704),
    'Padang Besar': (6.6601, 100.3214),
    'Kuala Perlis': (6.4000, 100.1333),
    'Kaki Bukit': (6.6333, 100.2167),
    'Chuping': (6.5000, 100.2333),
}

KEDAH_LOCATIONS = {
    'Alor Setar': (6.1248, 100.3678),
    'Sungai Petani': (5.6470, 100.4877),
    'Kulim': (5.3650, 100.5620),
    'Langkawi': (6.3500, 99.8000),
    'Pulau Langkawi Cable Car': (6.3850, 99.6650),
    'Gunung Jerai': (5.7800, 100.4300),
    'Baling': (5.6770, 100.9190),
    'Sik': (5.8230, 100.7260),
    'Yan': (5.7990, 100.3640),
    'Pendang': (5.9980, 100.4920),
    'Pokok Sena': (6.1660, 100.4800),
    'Kubang Pasu': (6.3200, 100.3500),
    'Kuala Nerang': (6.2500, 100.5333),
    'Jeniang': (5.8167, 100.6500),
    'Bedong': (5.7260, 100.5060),
    'Gurun': (5.8240, 100.4880),
    'Kota Kuala Muda': (5.5850, 100.3770),
    'Merbok': (5.7020, 100.4150),
    'Lembah Bujang': (5.7200, 100.4200),
    'Gunung Bintang': (5.6000, 100.8500),
}

PENANG_LOCATIONS = {
    'George Town': (5.4141, 100.3288),
    'Bayan Lepas': (5.2945, 100.2655),
    'Batu Ferringhi': (5.4700, 100.2400),
    'Penang Hill': (5.4200, 100.2700),
    'Kek Lok Si Temple': (5.3990, 100.2740),
    'Gurney Drive': (5.4360, 100.3100),
    'Butterworth': (5.3990, 100.3660),
    'Bukit Mertajam': (5.3630, 100.4670),
    'Nibong Tebal': (5.1660, 100.4770),
    'Kepala Batas': (5.5160, 100.4280),
    'Tanjung Bungah': (5.4650, 100.2850),
    'Teluk Bahang': (5.4610, 100.2160),
    'Balik Pulau': (5.3500, 100.2330),
    'Air Itam': (5.4020, 100.2820),
}

PERAK_LOCATIONS = {
    'Ipoh': (4.5975, 101.0901),
    'Taiping': (4.8500, 100.7333),
    'Teluk Intan': (4.0255, 101.0213),
    'Kuala Kangsar': (4.7667, 100.9333),
    'Kampar': (4.3167, 101.1500),
    'Sitiawan': (4.2167, 100.7000),
    'Lumut': (4.2333, 100.6333),
    'Pangkor Island': (4.2222, 100.5556),
    'Maxwell Hill (Bukit Larut)': (4.8600, 100.7500),
    'Gopeng': (4.4667, 101.1667),
    'Batu Gajah': (4.4667, 101.0500),
    'Gerik': (5.4167, 101.1333),
    'Lenggong': (5.1000, 100.9667),
    'Sungai Siput': (4.8500, 101.0833),
    'Parit Buntar': (5.1167, 100.4833),
    'Bagan Serai': (5.0167, 100.5333),
    'Tanjung Malim': (3.6833, 101.5167),
    'Slim River': (3.8333, 101.4000),
    'Tapah': (4.2000, 101.2667),
    'Cameron Highlands': (4.4700, 101.3800),
    'Brinchang': (4.5000, 101.3833),
    'Tanah Rata': (4.4667, 101.3833),
    'Kuala Kurau': (5.0167, 100.4333),
    'Pantai Remis': (4.4500, 100.6333),
    'Beruas': (4.5000, 100.7833),
    'Kuala Sepetang': (4.8333, 100.6333),
    'Selama': (5.2333, 100.6833),
}

KELANTAN_LOCATIONS = {
    'Kota Bharu': (6.1254, 102.2381),
    'Pasir Puteh': (5.8333, 102.4000),
    'Tumpat': (6.1980, 102.1700),
    'Wakaf Bharu': (6.1167, 102.2000),
    'Kubang Kerian': (6.0833, 102.2833),
    'Bachok': (6.0500, 102.4000),
    'Pasir Mas': (6.0500, 102.1333),
    'Tanah Merah': (5.8000, 102.1500),
    'Machang': (5.7667, 102.2167),
    'Kuala Krai': (5.5333, 102.2000),
    'Gua Musang': (4.8833, 101.9667),
    'Jeli': (5.7000, 101.8333),
    'Rantau Panjang': (6.0167, 101.9833),
    'Pengkalan Kubor': (6.1333, 102.0833),
}

TERENGGANU_LOCATIONS = {
    'Kuala Terengganu': (5.3302, 103.1408),
    'Kuala Nerus': (5.3833, 103.0833),
    'Marang': (5.2000, 103.2000),
    'Dungun': (4.7500, 103.4167),
    'Kemaman': (4.2333, 103.4167),
    'Chukai': (4.2333, 103.4167),
    'Paka': (4.6333, 103.4333),
    'Kerteh': (4.5167, 103.4500),
    'Setiu': (5.4667, 102.9333),
    'Besut': (5.7500, 102.5500),
    'Jerteh': (5.7333, 102.5000),
    'Kuala Besut': (5.8333, 102.5667),
    'Pulau Perhentian': (5.9167, 102.7333),
    'Pulau Redang': (5.7833, 103.0167),
    'Pulau Kapas': (5.2167, 103.2667),
    'Pulau Lang Tengah': (5.7833, 102.9000),
    'Kuala Berang': (5.0667, 102.9333),
    'Hulu Terengganu': (5.0500, 102.9167),
}

PAHANG_LOCATIONS = {
    'Kuantan': (3.8077, 103.3260),
    'Temerloh': (3.4500, 102.4167),
    'Bentong': (3.5167, 101.9000),
    'Kuala Lipis': (4.1833, 102.0500),
    'Jerantut': (3.9333, 102.3667),
    'Mentakab': (3.4833, 102.3500),
    'Raub': (3.7833, 101.8500),
    'Cameron Highlands (Pahang side)': (4.4700, 101.3800),
    'Genting Highlands': (3.4236, 101.7939),
    'Bukit Tinggi': (3.3500, 101.8300),
    'Fraser\'s Hill (Bukit Fraser)': (3.7167, 101.7333),
    'Taman Negara': (4.5000, 102.4000),
    'Kuala Tahan': (4.3833, 102.4000),
    'Cherating': (4.1167, 103.3833),
    'Balok': (3.9333, 103.3667),
    'Gambang': (3.7000, 103.1000),
    'Pekan': (3.4833, 103.4000),
    'Rompin': (2.7000, 103.5000),
    'Kuala Rompin': (2.8167, 103.4833),
    'Tioman Island': (2.7833, 104.1667),
    'Pulau Tioman': (2.7900, 104.1700),
    'Cameron Highlands - Brinchang': (4.5333, 101.3833),
    'Bukit Fraser - Jeriau': (3.7167, 101.7333),
    'Sungai Lembing': (3.9167, 103.0333),
    'Sungai Pandan Waterfall': (3.8167, 103.2833),
    'Pulau Aur': (2.4500, 104.5333),
}

SELANGOR_LOCATIONS = {
    'Shah Alam': (3.0733, 101.5185),
    'Petaling Jaya': (3.1073, 101.6067),
    'Subang Jaya': (3.0567, 101.5851),
    'Klang': (3.0333, 101.4500),
    'Kajang': (2.9833, 101.7833),
    'Ampang': (3.1500, 101.7667),
    'Cheras': (3.0500, 101.7667),
    'Selayang': (3.2500, 101.6500),
    'Rawang': (3.3167, 101.5833),
    'Kuala Selangor': (3.3500, 101.2500),
    'Sabak Bernam': (3.7667, 100.9833),
    'Sekinchan': (3.5167, 101.1000),
    'Tanjung Karang': (3.4167, 101.1833),
    'Banting': (2.8167, 101.5000),
    'Port Klang': (3.0000, 101.4000),
    'Pulau Ketam': (3.0333, 101.2500),
    'Hulu Langat': (3.1000, 101.8167),
    'Batang Kali': (3.4667, 101.6500),
    'Bukit Kutu': (3.5833, 101.7333),
    'Puncak Alam': (3.2333, 101.4167),
    'Puncak Perdana': (3.2167, 101.5000),
    'Cyberjaya': (2.9213, 101.6559),
    'Putrajaya': (2.9264, 101.6964),
    'Sepang': (2.7000, 101.7500),
    'Morib': (2.7500, 101.4500),
    'Genting Highlands (Selangor side)': (3.4236, 101.7939),
    'Pulau Carey': (2.9000, 101.3500),
    'Bukit Melawati': (3.3500, 101.2500),
    'Gombak': (3.2500, 101.7000),
}

KUALA_LUMPUR_LOCATIONS = {
    'KLCC': (3.1579, 101.7116),
    'Bukit Bintang': (3.1478, 101.7111),
    'KL Tower': (3.1528, 101.7033),
    'Merdeka Square': (3.1478, 101.6947),
    'National Mosque': (3.1417, 101.6917),
    'Batu Caves': (3.2379, 101.6840),
    'Bukit Nanas': (3.1500, 101.7000),
    'Titiwangsa': (3.1833, 101.7000),
    'Bukit Jalil': (3.0583, 101.6833),
    'Cheras (KL)': (3.0500, 101.7500),
    'Wangsa Maju': (3.2000, 101.7333),
    'Setiawangsa': (3.1833, 101.7500),
    'Kepong': (3.2167, 101.6333),
    'Segambut': (3.1833, 101.6667),
    'Damansara Heights': (3.1500, 101.6500),
    'Bangsar': (3.1167, 101.6667),
    'Sri Hartamas': (3.1667, 101.6500),
    'Mont Kiara': (3.1667, 101.6500),
}

NEGERI_SEMBILAN_LOCATIONS = {
    'Seremban': (2.7258, 101.9424),
    'Port Dickson': (2.5167, 101.8000),
    'Nilai': (2.8000, 101.8000),
    'Bahau': (2.8000, 102.4000),
    'Kuala Pilah': (2.7333, 102.2500),
    'Tampin': (2.4667, 102.2333),
    'Gemas': (2.5833, 102.6167),
    'Rembau': (2.5833, 102.1000),
    'Jelebu': (3.0500, 102.0500),
    'Jempol': (2.8667, 102.3667),
    'Gunung Ledang (Mount Ophir)': (2.3733, 102.6072),
    'Tanjung Tuan (Cape Rachado)': (2.4167, 101.8500),
    'Pantai Cahaya Negeri': (2.5000, 101.8167),
    'Ulu Bendul': (2.7000, 102.1000),
    'Genting Peras': (2.7833, 102.1000),
    'Sungai Menyala': (2.4667, 101.8500),
    'Bukit Putus': (2.6833, 102.0167),
}

MELAKA_LOCATIONS = {
    'Melaka City Center': (2.1896, 102.2501),
    'Ayer Keroh': (2.2667, 102.2833),
    'Alor Gajah': (2.3833, 102.2167),
    'Jasin': (2.3167, 102.4333),
    'Masjid Tanah': (2.3500, 102.1000),
    'Merlimau': (2.1500, 102.4167),
    'Sungai Udang': (2.2833, 102.1333),
    'Batu Berendam': (2.2500, 102.2333),
    'Klebang': (2.2167, 102.1833),
    'Tanjung Kling': (2.2333, 102.1500),
    'Pulau Besar': (2.1167, 102.3333),
    'Pulau Upeh': (2.1833, 102.2000),
    'Bandar Hilir': (2.1919, 102.2471),
    'Ayer Molek': (2.2167, 102.3167),
    'Durian Tunggal': (2.3167, 102.2833),
}

JOHOR_LOCATIONS = {
    'Johor Bahru': (1.4927, 103.7414),
    'Iskandar Puteri': (1.4230, 103.6300),
    'Kulai': (1.6667, 103.6000),
    'Skudai': (1.5333, 103.6667),
    'Pasir Gudang': (1.4667, 103.8833),
    'Kota Tinggi': (1.7333, 103.9000),
    'Mersing': (2.4333, 103.8333),
    'Batu Pahat': (1.8500, 102.9333),
    'Muar': (2.0500, 102.5667),
    'Segamat': (2.5000, 102.8167),
    'Kluang': (2.0333, 103.3167),
    'Pontian': (1.4833, 103.3833),
    'Kukup': (1.3333, 103.4667),
    'Pulau Tioman (Johor side)': (2.7900, 104.1700),
    'Pulau Aur': (2.4500, 104.5333),
    'Pulau Pemanggil': (2.5667, 104.3333),
    'Pulau Sibu': (2.2167, 104.1500),
    'Pulau Tinggi': (2.3000, 104.1167),
    'Endau-Rompin National Park': (2.5500, 103.3500),
    'Gunung Ledang (Johor side)': (2.3733, 102.6072),
    'Desaru': (1.5500, 104.2667),
    'Pengerang': (1.3667, 104.2000),
    'Tanjung Balau': (1.5500, 104.2500),
    'Tanjung Piai': (1.2667, 103.5167),
    'Gunung Panti': (1.8500, 103.7000),
    'Gunung Pulai': (1.6167, 103.5500),
    'Bekok': (2.3000, 103.1167),
    'Yong Peng': (2.0167, 103.0667),
    'Ayer Hitam': (1.9167, 103.1833),
    'Simpang Renggam': (1.8333, 103.3167),
    'Paloh': (2.1333, 103.2333),
    'Labis': (2.3833, 103.0167),
    'Chaah': (2.2500, 103.0500),
    'Bukit Kepong': (2.3333, 102.6667),
    'Pagoh': (2.1500, 102.7667),
    'Tangkak': (2.2667, 102.5500),
    'Gemas (Johor side)': (2.5833, 102.6167),
    'Bandar Penawar': (1.5333, 104.2333),
}

WEST_MALAYSIA_LOCATIONS = {
    **PERLIS_LOCATIONS,
    **KEDAH_LOCATIONS,
    **PENANG_LOCATIONS,
    **PERAK_LOCATIONS,
    **KELANTAN_LOCATIONS,
    **TERENGGANU_LOCATIONS,
    **PAHANG_LOCATIONS,
    **SELANGOR_LOCATIONS,
    **KUALA_LUMPUR_LOCATIONS,
    **NEGERI_SEMBILAN_LOCATIONS,
    **MELAKA_LOCATIONS,
    **JOHOR_LOCATIONS,
}

STARGAZING_CANDIDATES = {
    'Cameron Highlands, Pahang': (4.4700, 101.3800),
    'Brinchang, Cameron Highlands': (4.5000, 101.3833),
    'Tanah Rata, Cameron Highlands': (4.4667, 101.3833),
    'Genting Highlands, Pahang': (3.4236, 101.7939),
    'Fraser\'s Hill (Bukit Fraser)': (3.7167, 101.7333),
    'Bukit Tinggi, Pahang': (3.3500, 101.8300),
    'Maxwell Hill (Bukit Larut), Perak': (4.8600, 100.7500),
    'Gunung Jerai, Kedah': (5.7800, 100.4300),
    'Penang Hill, Penang': (5.4200, 100.2700),
    'Taman Negara, Pahang': (4.5000, 102.4000),
    'Kuala Tahan, Taman Negara': (4.3833, 102.4000),
    'Royal Belum State Park, Perak': (5.5500, 101.4000),
    'Endau-Rompin National Park, Johor': (2.5500, 103.3500),
    'Gunung Ledang (Mount Ophir), Johor': (2.3733, 102.6072),
    'Pulau Tioman, Pahang': (2.7900, 104.1700),
    'Pulau Redang, Terengganu': (5.7833, 103.0167),
    'Pulau Perhentian, Terengganu': (5.9167, 102.7333),
    'Pulau Kapas, Terengganu': (5.2167, 103.2667),
    'Pulau Langkawi, Kedah': (6.3500, 99.8000),
    'Pulau Pangkor, Perak': (4.2222, 100.5556),
    'Desaru Coast, Johor': (1.5500, 104.2667),
    'Mersing, Johor': (2.4333, 103.8333),
    'Kukup, Johor': (1.3333, 103.4667),
    'Tanjung Piai, Johor': (1.2667, 103.5167),
    'Kuala Selangor, Selangor': (3.3500, 101.2500),
    'Sekinchan, Selangor': (3.5167, 101.1000),
    'Pantai Cahaya Negeri, N. Sembilan': (2.5000, 101.8167),
    'Tanjung Tuan, N. Sembilan': (2.4167, 101.8500),
    'Sungai Lembing, Pahang': (3.9167, 103.0333),
    'Cherating, Pahang': (4.1167, 103.3833),
    'Kuala Rompin, Pahang': (2.8167, 103.4833),
    'Hulu Langat, Selangor': (3.1000, 101.8167),
    'Batang Kali, Selangor': (3.4667, 101.6500),
    'Bukit Kutu, Selangor': (3.5833, 101.7333),
    'Pulau Ketam, Selangor': (3.0333, 101.2500),
    'Gua Musang, Kelantan': (4.8833, 101.9667),
    'Kuala Berang, Terengganu': (5.0667, 102.9333),
    'Jerantut, Pahang': (3.9333, 102.3667),
    'Raub, Pahang': (3.7833, 101.8500),
    'Kuala Lipis, Pahang': (4.1833, 102.0500),
    'Gerik, Perak': (5.4167, 101.1333),
    'Lenggong, Perak': (5.1000, 100.9667),
    'Baling, Kedah': (5.6770, 100.9190),
    'Sik, Kedah': (5.8230, 100.7260),
    'Gunung Bintang, Kedah': (5.6000, 100.8500),
    'Pulau Sibu, Johor': (2.2167, 104.1500),
    'Pulau Tinggi, Johor': (2.3000, 104.1167),
    'Pulau Pemanggil, Johor': (2.5667, 104.3333),
    'Pulau Aur, Johor': (2.4500, 104.5333),
    'Pulau Besar, Melaka': (2.1167, 102.3333),
    'Gunung Nuang (Forest Reserve)': (3.2300, 101.8700),
}

# ============================================================================
# STATIC FALLBACK DATA (unchanged)
# ============================================================================

STATIC_AIRPORTS = {
    'KLIA (Kuala Lumpur International)': (2.7456, 101.7099),
    'KLIA2': (2.7433, 101.6855),
    'Subang Airport (SZB)': (3.1306, 101.5492),
    'Penang International Airport': (5.2971, 100.2767),
    'Langkawi International Airport': (6.3297, 99.7286),
    'Alor Setar Airport': (6.1897, 100.3983),
    'Ipoh Airport': (4.5679, 101.0922),
    'Kuantan Airport': (3.7753, 103.2093),
    'Kota Bharu Airport': (6.1668, 102.2928),
    'Kuala Terengganu Airport': (5.3825, 103.1028),
    'Senai Airport (Johor Bahru)': (1.6413, 103.6698),
    'Melaka International Airport': (2.2633, 102.2515),
    'Tioman Airport': (2.8183, 104.1600),
    'Redang Airport': (5.7650, 103.0053),
    'Pangkor Airport': (4.2457, 100.5526),
    'Taiping Airport': (4.8667, 100.7167),
    'Kerteh Airport': (4.5373, 103.4266),
    'Gong Kedak Airport': (5.7990, 102.4910),
    'Sungai Petani Airport': (5.6397, 100.4628),
    'Bayan Lepas Airport': (5.2971, 100.2767),
    'Kuala Pilah Airport': (2.7500, 102.2000),
    'Batu Berendam Airport': (2.2633, 102.2515),
}

STATIC_SETTLEMENTS = {
    'Kuala Lumpur': {'coords': (3.1390, 101.6869), 'population': 1800000},
    'George Town (Penang)': {'coords': (5.4141, 100.3288), 'population': 700000},
    'Ipoh': {'coords': (4.5975, 101.0901), 'population': 650000},
    'Shah Alam': {'coords': (3.0733, 101.5185), 'population': 650000},
    'Johor Bahru': {'coords': (1.4927, 103.7414), 'population': 500000},
    'Petaling Jaya': {'coords': (3.1073, 101.6067), 'population': 620000},
    'Kuantan': {'coords': (3.8077, 103.3260), 'population': 450000},
    'Kuala Terengganu': {'coords': (5.3302, 103.1408), 'population': 400000},
    'Kota Bharu': {'coords': (6.1254, 102.2381), 'population': 500000},
    'Alor Setar': {'coords': (6.1248, 100.3678), 'population': 400000},
    'Melaka City': {'coords': (2.1896, 102.2501), 'population': 500000},
    'Seremban': {'coords': (2.7258, 101.9424), 'population': 350000},
    'Sungai Petani': {'coords': (5.6470, 100.4877), 'population': 450000},
    'Kulai': {'coords': (1.6667, 103.6000), 'population': 250000},
    'Klang': {'coords': (3.0333, 101.4500), 'population': 240000},
    'Taiping': {'coords': (4.8500, 100.7333), 'population': 250000},
    'Teluk Intan': {'coords': (4.0255, 101.0213), 'population': 230000},
    'Kuala Kangsar': {'coords': (4.7667, 100.9333), 'population': 160000},
    'Batu Pahat': {'coords': (1.8500, 102.9333), 'population': 400000},
    'Muar': {'coords': (2.0500, 102.5667), 'population': 250000},
    'Kluang': {'coords': (2.0333, 103.3167), 'population': 220000},
    'Kota Tinggi': {'coords': (1.7333, 103.9000), 'population': 200000},
    'Pasir Gudang': {'coords': (1.4667, 103.8833), 'population': 200000},
    'Skudai': {'coords': (1.5333, 103.6667), 'population': 180000},
    'Iskandar Puteri': {'coords': (1.4230, 103.6300), 'population': 200000},
    'Temerloh': {'coords': (3.4500, 102.4167), 'population': 160000},
    'Mentakab': {'coords': (3.4833, 102.3500), 'population': 100000},
    'Bentong': {'coords': (3.5167, 101.9000), 'population': 100000},
    'Jerantut': {'coords': (3.9333, 102.3667), 'population': 60000},
    'Dungun': {'coords': (4.7500, 103.4167), 'population': 150000},
    'Kemaman': {'coords': (4.2333, 103.4167), 'population': 180000},
    'Marang': {'coords': (5.2000, 103.2000), 'population': 50000},
    'Besut': {'coords': (5.7500, 102.5500), 'population': 80000},
    'Tumpat': {'coords': (6.1980, 102.1700), 'population': 60000},
    'Pasir Mas': {'coords': (6.0500, 102.1333), 'population': 50000},
    'Kangar': {'coords': (6.4414, 100.1986), 'population': 60000},
    'Arau': {'coords': (6.4294, 100.2704), 'population': 30000},
    'Langkawi': {'coords': (6.3500, 99.8000), 'population': 50000},
    'Kulim': {'coords': (5.3650, 100.5620), 'population': 250000},
    'Bayan Lepas': {'coords': (5.2945, 100.2655), 'population': 150000},
    'Butterworth': {'coords': (5.3990, 100.3660), 'population': 200000},
    'Bukit Mertajam': {'coords': (5.3630, 100.4670), 'population': 200000},
    'Nibong Tebal': {'coords': (5.1660, 100.4770), 'population': 100000},
    'Kampar': {'coords': (4.3167, 101.1500), 'population': 90000},
    'Sitiawan': {'coords': (4.2167, 100.7000), 'population': 100000},
    'Lumut': {'coords': (4.2333, 100.6333), 'population': 30000},
    'Batu Gajah': {'coords': (4.4667, 101.0500), 'population': 80000},
    'Gopeng': {'coords': (4.4667, 101.1667), 'population': 60000},
    'Nilai': {'coords': (2.8000, 101.8000), 'population': 150000},
    'Port Dickson': {'coords': (2.5167, 101.8000), 'population': 100000},
    'Bahau': {'coords': (2.8000, 102.4000), 'population': 50000},
    'Tampin': {'coords': (2.4667, 102.2333), 'population': 40000},
    'Alor Gajah': {'coords': (2.3833, 102.2167), 'population': 60000},
    'Jasin': {'coords': (2.3167, 102.4333), 'population': 50000},
    'Putrajaya': {'coords': (2.9264, 101.6964), 'population': 100000},
    'Cyberjaya': {'coords': (2.9213, 101.6559), 'population': 50000},
    'Kajang': {'coords': (2.9833, 101.7833), 'population': 350000},
    'Ampang': {'coords': (3.1500, 101.7667), 'population': 400000},
    'Selayang': {'coords': (3.2500, 101.6500), 'population': 300000},
    'Rawang': {'coords': (3.3167, 101.5833), 'population': 250000},
    'Kuala Selangor': {'coords': (3.3500, 101.2500), 'population': 30000},
    'Sabak Bernam': {'coords': (3.7667, 100.9833), 'population': 20000},
    'Sekinchan': {'coords': (3.5167, 101.1000), 'population': 25000},
    'Banting': {'coords': (2.8167, 101.5000), 'population': 80000},
    'Sepang': {'coords': (2.7000, 101.7500), 'population': 100000},
    'Cameron Highlands (Tanah Rata)': {'coords': (4.4667, 101.3833), 'population': 20000},
    'Genting Highlands': {'coords': (3.4236, 101.7939), 'population': 5000},
    'Fraser\'s Hill': {'coords': (3.7167, 101.7333), 'population': 3000},
    'Gunung Ledang': {'coords': (2.3733, 102.6072), 'population': 2000},
    'Endau-Rompin': {'coords': (2.5500, 103.3500), 'population': 1000},
    'Tioman Island': {'coords': (2.7900, 104.1700), 'population': 3000},
    'Pulau Redang': {'coords': (5.7833, 103.0167), 'population': 2000},
    'Pulau Perhentian': {'coords': (5.9167, 102.7333), 'population': 2000},
    'Taman Negara': {'coords': (4.5000, 102.4000), 'population': 500},
    'Mersing': {'coords': (2.4333, 103.8333), 'population': 20000},
    'Desaru': {'coords': (1.5500, 104.2667), 'population': 5000},
    'Kukup': {'coords': (1.3333, 103.4667), 'population': 3000},
    'Tanjung Piai': {'coords': (1.2667, 103.5167), 'population': 500},
}

STARGAZING_FACILITY_TAGS = {
    'observatory': [('amenity', 'observatory'), ('man_made', 'observatory')],
    'hotel': [('tourism', 'hotel'), ('tourism', 'guest_house'), ('tourism', 'resort')],
    'campsite': [('tourism', 'camp_site'), ('tourism', 'caravan_site')],
    'viewpoint': [('tourism', 'viewpoint'), ('tourism', 'attraction')],
    'restaurant': [('amenity', 'restaurant'), ('amenity', 'cafe')],
    'fuel': [('amenity', 'fuel'), ('amenity', 'charging_station')],
    'hospital': [('amenity', 'hospital'), ('amenity', 'clinic')],
    'parking': [('amenity', 'parking')],
}

# ============================================================================
# DATA CLASSES (unchanged)
# ============================================================================

@dataclass
class Location:
    lat: float
    lon: float
    name: str = ""
    properties: Dict = field(default_factory=dict)

@dataclass
class AnalysisStep:
    step_number: int
    name: str
    description: str
    status: str = "pending"
    result: Any = None
    execution_time: float = 0.0
    reasoning: str = ""

@dataclass
class AnalysisResult:
    query: str
    steps: List[AnalysisStep] = field(default_factory=list)
    final_result: Any = None
    total_time: float = 0.0
    timestamp: str = ""
    success: bool = False

@dataclass
class MemoryEntry:
    query: str
    query_embedding: List[float] = field(default_factory=list)
    result_summary: str = ""
    success: bool = False
    execution_time: float = 0.0
    timestamp: str = ""
    parameters_used: Dict = field(default_factory=dict)

# ============================================================================
# REPOSITORY PATTERN (unchanged)
# ============================================================================

class MemoryRepository:
    def __init__(self, db_path: str = "starview_west_malaysia_memory.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                result_summary TEXT,
                success INTEGER,
                execution_time REAL,
                parameters TEXT,
                timestamp TEXT,
                embedding BLOB
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_type TEXT NOT NULL,
                parameter_name TEXT NOT NULL,
                optimal_value TEXT,
                success_rate REAL,
                usage_count INTEGER DEFAULT 1,
                last_updated TEXT
            )
        """)
        conn.commit()
        conn.close()

    def store_analysis(self, entry: MemoryEntry):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query_hash = hashlib.md5(entry.query.lower().encode()).hexdigest()
        cursor.execute("""
            INSERT INTO analysis_memory
            (query, query_hash, result_summary, success, execution_time, parameters, timestamp, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry.query, query_hash, entry.result_summary,
            1 if entry.success else 0, entry.execution_time,
            json.dumps(entry.parameters_used), entry.timestamp,
            pickle.dumps(entry.query_embedding)
        ))
        conn.commit()
        conn.close()

    def get_all_analyses(self, limit: int = 20) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_memory ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                'query': row[1],
                'result_summary': row[3],
                'success': bool(row[4]),
                'execution_time': row[5],
                'parameters': json.loads(row[6]) if row[6] else {},
                'timestamp': row[7]
            })
        conn.close()
        return results

    def find_similar_analyses(self, query: str, limit: int = 5) -> List[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM analysis_memory ORDER BY timestamp DESC LIMIT 100")
        rows = cursor.fetchall()
        if not query or not query.strip():
            conn.close()
            return []
        keywords = query.lower().split()
        results = []
        for row in rows:
            stored_query = row[1].lower()
            match_score = sum(1 for kw in keywords if kw in stored_query)
            if match_score > 0:
                results.append({
                    'query': row[1],
                    'result_summary': row[3],
                    'success': bool(row[4]),
                    'execution_time': row[5],
                    'parameters': json.loads(row[6]) if row[6] else {},
                    'timestamp': row[7],
                    'match_score': match_score
                })
        conn.close()
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:limit]

    def get_learned_parameter(self, analysis_type: str, parameter_name: str) -> Optional[str]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT optimal_value, success_rate FROM learned_parameters
            WHERE analysis_type = ? AND parameter_name = ?
            ORDER BY success_rate DESC LIMIT 1
        """, (analysis_type, parameter_name))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def update_learned_parameter(self, analysis_type: str, parameter_name: str,
                                  value: str, success: bool):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, success_rate, usage_count FROM learned_parameters
            WHERE analysis_type = ? AND parameter_name = ? AND optimal_value = ?
        """, (analysis_type, parameter_name, value))
        row = cursor.fetchone()
        if row:
            new_count = row[2] + 1
            new_rate = ((row[1] * row[2]) + (1 if success else 0)) / new_count
            cursor.execute("""
                UPDATE learned_parameters
                SET success_rate = ?, usage_count = ?, last_updated = ?
                WHERE id = ?
            """, (new_rate, new_count, datetime.now().isoformat(), row[0]))
        else:
            cursor.execute("""
                INSERT INTO learned_parameters
                (analysis_type, parameter_name, optimal_value, success_rate, usage_count, last_updated)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (analysis_type, parameter_name, value, 1.0 if success else 0.0, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    def get_analysis_stats(self) -> Dict:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM analysis_memory")
        total = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM analysis_memory WHERE success = 1")
        successful = cursor.fetchone()[0]
        cursor.execute("SELECT AVG(execution_time) FROM analysis_memory")
        avg_time = cursor.fetchone()[0] or 0
        conn.close()
        return {
            'total_analyses': total,
            'successful_analyses': successful,
            'success_rate': successful / total if total > 0 else 0,
            'avg_execution_time': avg_time
        }

# ============================================================================
# STRATEGY PATTERN
# ============================================================================

class AnalysisStrategy(ABC):
    @abstractmethod
    def analyse(self, location: Location, params: Dict) -> Dict:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass


class StargazingSuitabilityStrategy(AnalysisStrategy):
    """HYBRID Strategy v3.2.7 — with WAQI distance validation."""

    def get_name(self) -> str:
        return "StarView Suitability Analysis v3.2.7 (West Malaysia)"

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        return R * 2 * math.asin(min(1, math.sqrt(a)))

    def _lookup_peak_elevation(self, name: str) -> Optional[float]:
        if not name:
            return None
        name_lower = name.lower()
        for peak_key, elev in PEAK_ELEVATIONS.items():
            if peak_key in name_lower:
                return float(elev)
        return None

    def _get_elevation_quick(self, location: Location) -> tuple:
        if location.name and location.name in CANDIDATE_ELEVATIONS:
            elev = CANDIDATE_ELEVATIONS[location.name]
            return self._elev_to_score(elev), float(elev), 'Curated elevation (verified)'
        
        peak_elev = self._lookup_peak_elevation(location.name)
        if peak_elev is not None:
            return self._elev_to_score(peak_elev), peak_elev, 'Peak elevation (auto-detected)'
        
        try:
            elevation_url = f"https://api.open-elevation.com/api/v1/lookup?locations={location.lat},{location.lon}"
            response = requests.get(elevation_url, timeout=3)
            data = response.json()
            elev = data['results'][0]['elevation']
            return self._elev_to_score(elev), float(elev), 'Live Elevation API'
        except Exception:
            lat, lon = location.lat, location.lon
            if lat > 4.3 and lat < 4.7 and lon > 101.2 and lon < 101.6:
                return 4.5, 1500, 'Fallback: Cameron Highlands'
            elif lat > 3.3 and lat < 3.6 and lon > 101.6 and lon < 101.9:
                return 4.5, 1700, 'Fallback: Genting Highlands'
            elif lat > 3.6 and lat < 3.85 and lon > 101.6 and lon < 101.85:
                return 4.5, 1500, 'Fallback: Fraser\'s Hill'
            elif lat > 4.7 and lat < 5.0 and lon > 100.6 and lon < 100.9:
                return 4.3, 1000, 'Fallback: Maxwell Hill'
            elif lat > 5.3 and lat < 5.5 and lon > 100.2 and lon < 100.4:
                return 4.0, 833, 'Fallback: Penang Hill'
            elif lat > 5.7 and lat < 5.9 and lon > 100.3 and lon < 100.5:
                return 4.3, 1217, 'Fallback: Gunung Jerai'
            elif lat > 4.3 and lat < 4.7 and lon > 102.2 and lon < 102.6:
                return 3.5, 200, 'Fallback: Taman Negara'
            else:
                return 2.5, 30, 'Fallback: Lowland area'

    def _elev_to_score(self, elev: float) -> float:
        if elev > 1000:
            return 5.0
        elif elev > 500:
            return 4.8
        elif elev > 200:
            return 4.3
        elif elev > 100:
            return 3.8
        elif elev > 50:
            return 3.3
        else:
            return 2.5

    def _check_protected_zone(self, location: Location) -> Optional[Dict]:
        best = None
        for name, (lat, lon, radius_km, designation, desc) in PROTECTED_DARK_SKY_ZONES.items():
            dist = self._haversine(location.lat, location.lon, lat, lon)
            if dist <= radius_km:
                is_inside = dist <= (radius_km * 0.4)
                candidate = {
                    'name': name,
                    'designation': designation,
                    'description': desc,
                    'distance_km': round(dist, 1),
                    'radius_km': radius_km,
                    'is_inside': is_inside,
                }
                if best is None:
                    best = candidate
                else:
                    best_priority = (0 if best['is_inside'] else 1, best['distance_km'])
                    cand_priority = (0 if is_inside else 1, dist)
                    if cand_priority < best_priority:
                        best = candidate
        return best

    def _get_weather(self, location: Location) -> Optional[Dict]:
        try:
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": location.lat,
                "longitude": location.lon,
                "current": "temperature_2m,relative_humidity_2m,cloud_cover,"
                           "visibility,wind_speed_10m,wind_direction_10m,dew_point_2m",
                "wind_speed_unit": "ms",
                "timezone": "auto",
            }
            r = requests.get(url, params=params, timeout=4)
            data = r.json()
            cur = data.get("current", {})
            visibility_m = cur.get("visibility")
            return {
                "temperature_c": cur.get("temperature_2m"),
                "humidity_pct": cur.get("relative_humidity_2m"),
                "cloud_cover_pct": cur.get("cloud_cover"),
                "visibility_km": visibility_m / 1000 if visibility_m else None,
                "wind_speed_ms": cur.get("wind_speed_10m"),
                "wind_direction_deg": cur.get("wind_direction_10m"),
                "dew_point_c": cur.get("dew_point_2m"),
                "source": "Open-Meteo (Live)",
                "time": cur.get("time"),
            }
        except Exception:
            return None

    def _score_cloud_cover(self, cloud_cover_pct: Optional[float]) -> tuple:
        if cloud_cover_pct is None:
            return 3.0, "Unknown", "Weather unavailable — neutral score"
        if cloud_cover_pct < 10:
            return 5.0, "Excellent", f"Crystal clear ({cloud_cover_pct:.0f}% cloud)"
        elif cloud_cover_pct < 25:
            return 4.5, "Very Good", f"Mostly clear ({cloud_cover_pct:.0f}% cloud)"
        elif cloud_cover_pct < 50:
            return 3.5, "Good", f"Partly cloudy ({cloud_cover_pct:.0f}% cloud)"
        elif cloud_cover_pct < 75:
            return 2.5, "Moderate", f"Mostly cloudy ({cloud_cover_pct:.0f}% cloud)"
        else:
            return 1.5, "Poor", f"Heavy cloud cover ({cloud_cover_pct:.0f}%)"

    def _geographic_score_light_pollution(self, location: Location, elevation_m: float) -> tuple:
        lat, lon = location.lat, location.lon
        total_light_pollution = 0.0
        for name, data in STATIC_SETTLEMENTS.items():
            s_lat, s_lon = data['coords']
            pop = data.get('population', 1000)
            dist = self._haversine(lat, lon, s_lat, s_lon)
            if dist > 200:
                continue
            if dist < 1:
                dist = 1
            contribution = (pop / 100000) / (dist ** 1.5)
            total_light_pollution += contribution
        
        if elevation_m > 1500 and total_light_pollution < 3.0:
            return 5.0, 0, 'Geographic: Above light dome (high alt)'
        if elevation_m > 1000 and total_light_pollution < 5.0:
            return 4.8, 1, 'Geographic: Highland dark sky'
        if elevation_m > 800 and total_light_pollution < 6.0:
            return 4.5, 1, 'Geographic: Highland dark sky'
        
        if total_light_pollution < 0.01:
            return 5.0, 0, 'Geographic: Pristine dark sky'
        elif total_light_pollution < 0.05:
            return 4.8, 1, 'Geographic: Very dark sky'
        elif total_light_pollution < 0.15:
            return 4.5, 2, 'Geographic: Dark sky'
        elif total_light_pollution < 0.4:
            return 4.0, 3, 'Geographic: Mostly dark'
        elif total_light_pollution < 0.8:
            return 3.5, 4, 'Geographic: Suburban sky'
        elif total_light_pollution < 1.5:
            return 3.0, 5, 'Geographic: Semi-dark'
        elif total_light_pollution < 3.0:
            return 2.0, 7, 'Geographic: Light pollution'
        elif total_light_pollution < 6.0:
            return 1.5, 8, 'Geographic: Significant light pollution'
        else:
            return 1.0, 10, 'Geographic: Heavy light pollution'

    def _geographic_score_atmospheric_clarity(self, location: Location, elevation_m: float) -> tuple:
        lat, lon = location.lat, location.lon

        if elevation_m > 1500:
            return 5.0, 80, 'Geographic: High-altitude (above clouds)'
        if elevation_m > 1000:
            return 4.7, 60, 'Geographic: High-altitude'

        if lon > 103.0:
            coastal_dist = 10
        elif lon < 100.5:
            coastal_dist = 10
        elif lon > 101.5 and lon < 102.5:
            coastal_dist = 40
        else:
            coastal_dist = 30

        if coastal_dist > 50:
            return 5.0, coastal_dist, 'Geographic: Deep inland'
        elif coastal_dist > 30:
            return 4.3, coastal_dist, 'Geographic: Inland'
        elif coastal_dist > 15:
            return 3.5, coastal_dist, 'Geographic: Coastal influence'
        else:
            return 2.5, coastal_dist, 'Geographic: Coastal'

    def _geographic_score_infrastructure(self, location: Location) -> tuple:
        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, coords in STATIC_AIRPORTS.items():
            a_lat, a_lon = coords
            dist = self._haversine(lat, lon, a_lat, a_lon)
            min_dist = min(min_dist, dist)
        details = {
            'airports': 1 if min_dist < 60 else 0,
            'major_roads': 2 if min_dist < 30 else 0,
            'power_facilities': 1 if min_dist < 40 else 0,
            'accommodation': 1 if min_dist < 20 else 0
        }
        if min_dist < 30:
            return 4.5, details, 'Geographic: Near airport'
        elif min_dist < 60:
            return 3.5, details, 'Geographic: Airport nearby'
        elif min_dist < 100:
            return 2.5, details, 'Geographic: Some access'
        else:
            return 1.5, details, 'Geographic: Remote'

    def _geographic_score_land(self, location: Location, protected_zone: Optional[Dict]) -> tuple:
        if protected_zone and protected_zone.get('is_inside'):
            details = {'forest_areas': 40, 'developed_areas': 1, 'open_areas': 30}
            return 5.0, details, 'Geographic: Protected park (vast land)'

        lat, lon = location.lat, location.lon
        min_dist = 999
        for name, data in STATIC_SETTLEMENTS.items():
            s_lat, s_lon = data['coords']
            dist = self._haversine(lat, lon, s_lat, s_lon)
            min_dist = min(min_dist, dist)
        details = {
            'forest_areas': 30 if min_dist > 50 else 10,
            'developed_areas': 2 if min_dist > 50 else 10,
            'open_areas': 40 if min_dist > 30 else 15
        }
        if min_dist > 80:
            return 5.0, details, 'Geographic: Abundant land'
        elif min_dist > 50:
            return 4.0, details, 'Geographic: Good land'
        elif min_dist > 30:
            return 3.0, details, 'Geographic: Moderate land'
        elif min_dist > 15:
            return 2.5, details, 'Geographic: Limited land'
        else:
            return 2.0, details, 'Geographic: Scarce land'

    def _geographic_score_cloud_risk(self, lat: float, lon: float, elevation_m: float, protected_zone: Optional[Dict]) -> tuple:
        if elevation_m < 50:
            return 3.0, 'Moderate', 'Geographic: Coastal (low elevation)'
        if elevation_m > 1500:
            return 4.5, 'Low', 'Geographic: Above cloud layer'
        if elevation_m > 1000:
            return 4.2, 'Low', 'Geographic: Highland climate'

        if protected_zone and protected_zone.get('is_inside'):
            return 4.3, 'Low', 'Geographic: Protected inland'

        if lon > 102.5:
            return 2.8, 'High', 'Geographic: East coast (monsoon)'
        elif lon > 101.0 and lon < 102.5 and lat > 3.0:
            return 4.0, 'Low', 'Geographic: Interior highland'
        else:
            return 3.2, 'Moderate', 'Geographic: Typical'

    def _score_latitudinal_advantage(self, lat: float) -> float:
        abs_lat = abs(lat)
        if abs_lat <= 3:
            return 5.0
        elif abs_lat <= 5:
            return 4.5
        elif abs_lat <= 7:
            return 4.2
        else:
            return 3.8

    def _try_osm_in_background(self, location: Location, radius: int) -> Optional[Dict]:
        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            results = {}
            query = f"""
            [out:json][timeout:5];
            (
              node["tourism"~"hotel|guest_house|resort|camp_site|viewpoint"](around:{radius},{location.lat},{location.lon});
            );
            out count;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=5)
            results['tourism_count'] = len(response.json().get('elements', []))

            query = f"""
            [out:json][timeout:5];
            (
              node["amenity"~"restaurant|cafe|fuel|parking"](around:{radius},{location.lat},{location.lon});
            );
            out count;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=5)
            results['amenities_count'] = len(response.json().get('elements', []))

            query = f"""
            [out:json][timeout:5];
            (
              way["highway"~"motorway|trunk|primary"](around:{radius},{location.lat},{location.lon});
            );
            out count;
            """
            response = requests.post(overpass_url, data={'data': query}, timeout=5)
            results['road_count'] = len(response.json().get('elements', []))
            return results
        except Exception:
            return None

    def analyse(self, location: Location, params: Dict) -> Dict:
        radius = params.get('radius', 10000)
        weights = params.get('weights', {
            'light_pollution': 0.22,
            'atmospheric_clarity': 0.18,
            'cloud_risk': 0.15,
            'cloud_cover': 0.12,
            'elevation': 0.10,
            'latitudinal_advantage': 0.08,
            'infrastructure_access': 0.08,
            'land_availability': 0.07,
        })

        scores = {}
        details = {}
        data_source_details = []
        osm_data = None
        osm_available = False
        weather_data = None
        air_quality_data = None
        haze_data = None

        elevation_score, elevation_m, elev_source = self._get_elevation_quick(location)
        protected_zone = self._check_protected_zone(location)

        # 1. LIGHT POLLUTION
        lp_score, lp_index, lp_source = self._geographic_score_light_pollution(location, elevation_m)
        if protected_zone and protected_zone.get('is_inside'):
            lp_score = max(lp_score, 4.7)
            lp_index = min(lp_index, 1)
            data_source_details.append(
                f"🏞️ Protected Zone (INSIDE): {protected_zone['name']} ({protected_zone['designation']})"
            )
            lp_source = f"Protected (inside): {protected_zone['name']}"
        elif protected_zone:
            data_source_details.append(
                f"🏞️ Near Protected Zone: {protected_zone['name']} (~{protected_zone['distance_km']:.1f} km)"
            )
        data_source_details.append(f"Light Pollution: {lp_source}")
        scores['light_pollution'] = lp_score
        details['light_pollution'] = {
            'score': lp_score,
            'value': f"Level {lp_index}/10" if not (protected_zone and protected_zone.get('is_inside')) else f"Level {lp_index}/10 (Protected)",
            'weight': weights['light_pollution'],
            'source': lp_source
        }

        # 2. ATMOSPHERIC CLARITY
        clarity_score, coastal_dist, clarity_source = self._geographic_score_atmospheric_clarity(location, elevation_m)
        data_source_details.append(f"Clarity: {clarity_source}")
        scores['atmospheric_clarity'] = clarity_score
        details['atmospheric_clarity'] = {
            'score': clarity_score,
            'value': f"{coastal_dist:.0f}km from coast" if elevation_m < 1000 else f"High altitude ({elevation_m:.0f}m)",
            'weight': weights['atmospheric_clarity'],
            'source': clarity_source
        }

        # 3. ELEVATION
        data_source_details.append(f"Elevation: {elev_source} ({elevation_m:.0f}m)")
        scores['elevation'] = elevation_score
        details['elevation'] = {
            'score': elevation_score,
            'value': f"{elevation_m:.0f}m",
            'weight': weights['elevation'],
            'source': elev_source
        }

        # 4. CLOUD RISK
        cloud_risk_score, cloud_risk, cloud_risk_source = self._geographic_score_cloud_risk(
            location.lat, location.lon, elevation_m, protected_zone
        )
        data_source_details.append(f"Cloud Risk: {cloud_risk_source}")
        scores['cloud_risk'] = cloud_risk_score
        details['cloud_risk'] = {
            'score': cloud_risk_score,
            'value': cloud_risk,
            'weight': weights['cloud_risk'],
            'source': cloud_risk_source
        }

        # 5. LATITUDE
        lat_score = self._score_latitudinal_advantage(location.lat)
        scores['latitudinal_advantage'] = lat_score
        details['latitudinal_advantage'] = {
            'score': lat_score,
            'value': f"{abs(location.lat):.1f}°{'N' if location.lat > 0 else 'S'}",
            'weight': weights['latitudinal_advantage'],
            'source': 'Geographic'
        }

        # 6. INFRASTRUCTURE
        infra_score, infra_details, infra_source = self._geographic_score_infrastructure(location)
        data_source_details.append(f"Infrastructure: {infra_source}")
        scores['infrastructure_access'] = infra_score
        details['infrastructure_access'] = {
            'score': infra_score,
            'value': infra_details,
            'weight': weights['infrastructure_access'],
            'source': infra_source
        }

        # 7. LAND
        land_score, land_details, land_source = self._geographic_score_land(location, protected_zone)
        data_source_details.append(f"Land: {land_source}")
        scores['land_availability'] = land_score
        details['land_availability'] = {
            'score': land_score,
            'value': land_details,
            'weight': weights['land_availability'],
            'source': land_source
        }

        # 8. CLOUD COVER (Live)
        weather_data = self._get_weather(location)
        if weather_data:
            cc = weather_data.get('cloud_cover_pct')
            cc_score, cc_rating, cc_explanation = self._score_cloud_cover(cc)
            data_source_details.append(f"Cloud Cover: {cc_explanation}")
            weather_data['cloud_rating'] = cc_rating
            weather_data['cloud_explanation'] = cc_explanation
        else:
            cc_score, cc_rating, cc_explanation = 3.0, "Unknown", "Weather unavailable"
            data_source_details.append("Cloud Cover: Weather API unavailable")

        scores['cloud_cover'] = cc_score
        details['cloud_cover'] = {
            'score': cc_score,
            'value': weather_data.get('cloud_cover_pct') and f"{weather_data['cloud_cover_pct']:.0f}%" or "N/A",
            'weight': weights['cloud_cover'],
            'source': weather_data.get('source', 'Unavailable') if weather_data else 'Unavailable'
        }

        # HAZE/FOG DETECTION (v3.2.7: uses merged air quality with distance check)
        air_quality_data = get_merged_air_quality({'lat': location.lat, 'lon': location.lon})
        haze_data = detect_haze(
            weather_data, 
            air_quality_data, 
            {'lat': location.lat, 'lon': location.lon, 'elevation_m': elevation_m}
        )
        
        if haze_data['detected']:
            if haze_data.get('is_fog'):
                fog_type_label = haze_data.get('fog_type', 'unknown')
                data_source_details.append(f"🌫️ Fog Detected: {fog_type_label} ({haze_data['confidence']} confidence)")
            else:
                data_source_details.append(f"🌫️ Haze Detected: {haze_data['severity']} ({haze_data['confidence']} confidence)")
        
        if air_quality_data:
            pm25 = air_quality_data.get('pm2_5')
            if pm25 is not None:
                src_label = air_quality_data.get('source', 'Air Quality API')
                data_source_details.append(f"Air Quality ({src_label}): PM2.5 {pm25:.1f} µg/m³")
            # v3.2.7: log WAQI cross-check if present
            waqi_pm25 = air_quality_data.get('waqi_pm25')
            om_pm25 = air_quality_data.get('openmeteo_pm25')
            if waqi_pm25 is not None and om_pm25 is not None:
                station = air_quality_data.get('waqi_station', 'ground station')
                dist = air_quality_data.get('waqi_station_distance_km')
                dist_note = f", {dist:.1f} km away" if dist is not None else ""
                data_source_details.append(
                    f"🌐 Air Quality Cross-Check: Open-Meteo {om_pm25:.1f} vs WAQI {waqi_pm25:.1f} µg/m³ ({station}{dist_note})"
                )

        # BASE SCORE
        total_score = sum(scores[key] * weights.get(key, 0) for key in scores.keys() if key in weights)
        max_possible = sum(weights.values()) * 5.0
        percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0

        # PENALTIES
        penalty = 0.0
        penalty_reasons = []

        if not (protected_zone and protected_zone.get('is_inside')):
            if lp_index >= 8:
                penalty += 20.0
                penalty_reasons.append(f"Heavy light pollution (Level {lp_index}/10): -20%")
            elif lp_index >= 5:
                penalty += 10.0
                penalty_reasons.append(f"Significant light pollution (Level {lp_index}/10): -10%")

        if cloud_risk == 'High' and elevation_m < 1000:
            penalty += 12.0
            penalty_reasons.append("High seasonal cloud risk: -12%")

        if coastal_dist < 10 and elevation_m < 500:
            penalty += 8.0
            penalty_reasons.append("Coastal location (cloud/haze risk): -8%")

        if weather_data and weather_data.get('cloud_cover_pct'):
            if weather_data['cloud_cover_pct'] > 70:
                penalty += 10.0
                penalty_reasons.append(f"Heavy cloud cover now ({weather_data['cloud_cover_pct']:.0f}%): -10%")

        haze_severity = haze_data.get('severity', 'None')
        is_fog = haze_data.get('is_fog', False)
        
        if is_fog:
            penalty += 8.0
            penalty_reasons.append(f"Natural mountain fog (viewing blocked): -8%")
        elif haze_severity == 'Severe':
            penalty += 25.0
            penalty_reasons.append(f"SEVERE HAZE detected: -25%")
        elif haze_severity == 'Heavy':
            penalty += 18.0
            penalty_reasons.append(f"Heavy haze detected: -18%")
        elif haze_severity == 'Moderate':
            penalty += 10.0
            penalty_reasons.append(f"Moderate haze detected: -10%")
        elif haze_severity == 'Light':
            penalty += 4.0
            penalty_reasons.append(f"Light haze detected: -4%")

        percentage = max(0.0, min(100.0, percentage - penalty))

        if percentage >= 80:
            rating, emoji, rec = 'Excellent', '🌟', 'World-class stargazing destination potential'
        elif percentage >= 65:
            rating, emoji, rec = 'Good', '✨', 'Excellent viewing site with minor improvements'
        elif percentage >= 50:
            rating, emoji, rec = 'Moderate', '⭐', 'Good viewing site requiring some investment'
        elif percentage >= 35:
            rating, emoji, rec = 'Limited', '⚠️', 'Challenging conditions, major investment needed'
        else:
            rating, emoji, rec = 'Poor', '❌', 'Not recommended for astronomy development'

        try:
            osm_data = self._try_osm_in_background(location, radius)
            if osm_data and any(v > 0 for v in osm_data.values()):
                osm_available = True
                data_source_details.append(
                    f"🌐 OSM: {osm_data.get('tourism_count', 0)} tourism, "
                    f"{osm_data.get('amenities_count', 0)} amenities"
                )
        except Exception:
            pass

        seen = set()
        unique_details = []
        for d in data_source_details:
            if d not in seen:
                seen.add(d)
                unique_details.append(d)

        return {
            'success': True,
            'scores': scores,
            'details': details,
            'weighted_score': total_score,
            'max_possible_score': max_possible,
            'suitability_percentage': round(percentage, 1),
            'base_percentage': round((total_score / max_possible * 100) if max_possible > 0 else 0, 1),
            'penalty_applied': round(penalty, 1),
            'penalty_reasons': penalty_reasons,
            'rating': rating,
            'rating_emoji': emoji,
            'recommendation': rec,
            'radius_used': radius,
            'location': f"{location.name or 'West Malaysia location'} ({location.lat:.4f}, {location.lon:.4f})",
            'location_name': location.name or 'West Malaysia location',
            'elevation_m': elevation_m,
            'light_pollution_index': lp_index,
            'coastal_distance_km': coastal_dist,
            'cloud_risk': cloud_risk,
            'lat_deg': abs(location.lat),
            'lon': location.lon,
            'lat': location.lat,
            'protected_zone': protected_zone,
            'data_sources': [d for d in unique_details],
            'data_source_details': unique_details,
            'used_osm': osm_available,
            'osm_data': osm_data if osm_available else None,
            'weather': weather_data,
            'cloud_cover_pct': weather_data.get('cloud_cover_pct') if weather_data else None,
            'humidity_pct': weather_data.get('humidity_pct') if weather_data else None,
            'visibility_km': weather_data.get('visibility_km') if weather_data else None,
            'temperature_c': weather_data.get('temperature_c') if weather_data else None,
            'dew_point_c': weather_data.get('dew_point_c') if weather_data else None,
            'wind_speed_ms': weather_data.get('wind_speed_ms') if weather_data else None,
            'wind_direction_deg': weather_data.get('wind_direction_deg') if weather_data else None,
            'haze': haze_data,
            'air_quality': air_quality_data,
            'used_fallback': True,
            'from_cache': False,
            'analysis_method': 'HYBRID v3.2.7 West Malaysia: WAQI-Distance-Validated + Peak Elevation + Inside/Near + Fog + Haze'
        }


class ProximityAnalysisStrategy(AnalysisStrategy):
    def get_name(self) -> str:
        return "Proximity Analysis"

    def analyse(self, location: Location, params: Dict) -> Dict:
        amenity_type = params.get('amenity_type', 'hotel')
        radius = params.get('radius', 5000)
        tags_to_query = STARGAZING_FACILITY_TAGS.get(amenity_type, [('amenity', amenity_type)])
        query_parts = []
        for key, value in tags_to_query:
            query_parts.append(f'node["{key}"="{value}"](around:{radius},{location.lat},{location.lon});')
            query_parts.append(f'way["{key}"="{value}"](around:{radius},{location.lat},{location.lon});')
        query_body = "\n".join(query_parts)
        query = f"""[out:json][timeout:45];
(
{query_body}
);
out center;"""
        try:
            headers = {'User-Agent': 'StarViewWestMalaysia/3.2.7'}
            response = requests.post("https://overpass-api.de/api/interpreter",
                                   data={'data': query}, headers=headers, timeout=45)
            response.raise_for_status()
            data = response.json()
            elements = data.get('elements', [])
            results = []
            seen_locations = set()
            for elem in elements:
                lat = elem.get('lat') or elem.get('center', {}).get('lat')
                lon = elem.get('lon') or elem.get('center', {}).get('lon')
                if lat and lon:
                    loc_key = f"{round(lat, 5)}_{round(lon, 5)}"
                    if loc_key not in seen_locations:
                        seen_locations.add(loc_key)
                        tags = elem.get('tags', {})
                        name = tags.get('name', tags.get('brand', 'Unknown'))
                        results.append({
                            'name': name, 'lat': lat, 'lon': lon,
                            'type': amenity_type, 'tags': tags
                        })
            return {
                'success': True, 'count': len(results),
                'amenities': results, 'radius': radius,
                'amenity_type': amenity_type,
                'location': f"West Malaysia ({location.lat:.4f}, {location.lon:.4f})"
            }
        except Exception as e:
            return {
                'success': False, 'error': str(e),
                'amenities': [], 'count': 0,
                'radius': radius, 'amenity_type': amenity_type
            }


class StrategySelector:
    _strategies = {
        'stargazing': StargazingSuitabilityStrategy,
        'proximity': ProximityAnalysisStrategy,
    }

    @classmethod
    def get_strategy(cls, strategy_type: str) -> AnalysisStrategy:
        strategy_class = cls._strategies.get(strategy_type)
        if not strategy_class:
            raise ValueError(f"Unknown strategy: {strategy_type}")
        return strategy_class()

    @classmethod
    def available_strategies(cls) -> List[str]:
        return list(cls._strategies.keys())

# ============================================================================
# RATE LIMITING
# ============================================================================

class RateLimiter:
    def __init__(self, calls_per_second: float = 0.5):
        self.calls_per_second = calls_per_second
        self.last_call = 0

    def wait(self):
        now = time.time()
        time_since_last = now - self.last_call
        min_interval = 1.0 / self.calls_per_second
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        self.last_call = time.time()

# ============================================================================
# MAIN AGENT CLASS (unchanged)
# ============================================================================

class StarViewWestMalaysiaAgent:
    def __init__(self):
        self.memory_repo = MemoryRepository()
        self.rate_limiter = RateLimiter(calls_per_second=0.5)
        self.short_term_memory: Dict[str, Any] = {}
        self.current_analysis: Optional[AnalysisResult] = None

    def reason_about_query(self, query: str) -> tuple:
        query_lower = query.lower()
        steps = []
        steps.append({
            'step': 'Understanding Query',
            'reasoning': f"Analysing stargazing site selection request: '{query}'",
            'action': 'parse_intent'
        })
        similar = self.memory_repo.find_similar_analyses(query, limit=3)
        if similar:
            steps.append({
                'step': 'Memory Recall',
                'reasoning': f"Found {len(similar)} similar past analyses.",
                'action': 'apply_learned_parameters',
                'prior_experience': similar[0]
            })
        analysis_type = 'stargazing'
        steps.append({
            'step': 'Strategy Selection',
            'reasoning': 'Using StarView Suitability strategy v3.2.7 with WAQI distance-validated cross-check.',
            'action': 'use_stargazing_strategy'
        })
        learned_radius = self.memory_repo.get_learned_parameter(analysis_type, 'radius')
        if learned_radius:
            steps.append({
                'step': 'Parameter Optimisation',
                'reasoning': f"Using learned radius of {learned_radius}m.",
                'action': 'apply_learned_radius',
                'value': learned_radius
            })
        else:
            steps.append({
                'step': 'Parameter Selection',
                'reasoning': 'Using default radius of 10km.',
                'action': 'use_default_radius',
                'value': '10000'
            })
        steps.append({'step': 'Moon Phase Calculation', 'reasoning': 'Calculating moon phase.', 'action': 'calculate_moon'})
        steps.append({'step': 'Milky Way Check', 'reasoning': 'Determining galactic core visibility.', 'action': 'check_milky_way'})
        steps.append({'step': 'Haze & Fog Analysis', 'reasoning': 'Checking for haze vs tropical/temperate fog.', 'action': 'detect_haze'})
        steps.append({'step': 'Air Quality Cross-Check', 'reasoning': 'Merging Open-Meteo CAMS + WAQI ground station (distance-validated).', 'action': 'merge_air_quality'})
        steps.append({'step': 'Execution Planning', 'reasoning': 'Ready to execute.', 'action': 'prepare_execution'})
        return steps, analysis_type

    def execute_analysis(self, location: Location, query: str,
                         params: Dict, progress_callback: Callable = None) -> AnalysisResult:
        start_time = time.time()
        result = AnalysisResult(query=query, timestamp=datetime.now().isoformat())
        reasoning_steps, analysis_type = self.reason_about_query(query)
        for i, step_info in enumerate(reasoning_steps):
            result.steps.append(AnalysisStep(
                step_number=i + 1,
                name=step_info['step'],
                description=step_info['reasoning'],
                status='completed',
                reasoning=step_info['reasoning']
            ))
        if progress_callback:
            progress_callback(0.3, "Reasoning complete, executing hybrid analysis...")
        try:
            strategy = StrategySelector.get_strategy(analysis_type)
            self.rate_limiter.wait()
            analysis_result = strategy.analyse(location, params)
            analysis_result['from_cache'] = False
            
            moon_phase = calculate_moon_phase()
            analysis_result['moon_phase'] = moon_phase
            
            milky_way = get_milky_way_visibility(location.lat, location.lon)
            analysis_result['milky_way'] = milky_way
            
            astro_scores = calculate_astrophotography_scores(analysis_result, moon_phase)
            analysis_result['astrophotography_scores'] = astro_scores
            
            if analysis_result.get('success'):
                used_osm = analysis_result.get('used_osm', False)
                protected = analysis_result.get('protected_zone')
                haze = analysis_result.get('haze', {})
                method_note = analysis_result.get('analysis_method', 'HYBRID v3.2.7 West Malaysia')
                if protected:
                    tag = 'INSIDE' if protected.get('is_inside') else 'NEAR'
                    method_note += f" | {tag} Protected: {protected['name']}"
                if haze.get('detected'):
                    if haze.get('is_fog'):
                        method_note += f" | FOG: {haze.get('fog_type', 'unknown')}"
                    else:
                        method_note += f" | HAZE: {haze['severity']}"
                if haze.get('ground_verified'):
                    method_note += f" | GROUND-VERIFIED"
                result.steps.append(AnalysisStep(
                    step_number=len(result.steps) + 1,
                    name="Data Source Validation",
                    description=f"Method: {method_note}",
                    status='completed',
                    reasoning=f"Used {'OSM + Geographic' if used_osm else 'Geographic'} rules"
                ))
            result.steps.append(AnalysisStep(
                step_number=len(result.steps) + 1,
                name=f"Execute {strategy.get_name()}",
                description=f"Running {analysis_type} analysis on {location.name or 'West Malaysia location'}",
                status='completed' if analysis_result.get('success') else 'failed',
                result=analysis_result,
                reasoning="Analysis complete"
            ))
            result.final_result = analysis_result
            result.success = analysis_result.get('success', False)
        except Exception as e:
            result.steps.append(AnalysisStep(
                step_number=len(result.steps) + 1,
                name="Analysis Execution",
                description="Executing spatial analysis",
                status='failed',
                reasoning=f"Error: {str(e)}"
            ))
            result.success = False
        if progress_callback:
            progress_callback(0.8, "Storing results in memory...")
        result.total_time = time.time() - start_time
        memory_entry = MemoryEntry(
            query=query,
            result_summary=str(result.final_result)[:500] if result.final_result else "",
            success=result.success,
            execution_time=result.total_time,
            timestamp=result.timestamp,
            parameters_used=params
        )
        self.memory_repo.store_analysis(memory_entry)
        if result.success:
            self.memory_repo.update_learned_parameter(
                analysis_type, 'radius', str(params.get('radius', 10000)), True
            )
        self.short_term_memory['last_analysis'] = result
        self.short_term_memory['last_location'] = location
        if progress_callback:
            progress_callback(1.0, "Complete")
        return result

# ============================================================================
# UI HELPERS
# ============================================================================

def init_session_state():
    if 'agent' not in st.session_state:
        st.session_state.agent = StarViewWestMalaysiaAgent()
    if 'analysis_history' not in st.session_state:
        st.session_state.analysis_history = []
    if 'selected_location' not in st.session_state:
        st.session_state.selected_location = Location(
            lat=4.4700, lon=101.3800, name="Cameron Highlands, Pahang"
        )
    if 'reasoning_log' not in st.session_state:
        st.session_state.reasoning_log = []
    if 'current_results' not in st.session_state:
        st.session_state.current_results = None
    if 'basemap_choice' not in st.session_state:
        st.session_state.basemap_choice = "OpenStreetMap"
    if 'show_radius_circle' not in st.session_state:
        st.session_state.show_radius_circle = True
    if 'comparison_mode' not in st.session_state:
        st.session_state.comparison_mode = False
    if 'candidate_scores' not in st.session_state:
        st.session_state.candidate_scores = {}


def render_region_selector():
    regions = {
        '🌏 All West Malaysia': 'all',
        '🏝️ Perlis': 'perlis',
        '🏝️ Kedah': 'kedah',
        '🏝️ Penang': 'penang',
        '🏝️ Perak': 'perak',
        '🏝️ Kelantan': 'kelantan',
        '🏝️ Terengganu': 'terengganu',
        '🏝️ Pahang': 'pahang',
        '🏝️ Selangor': 'selangor',
        '🏝️ Kuala Lumpur': 'kl',
        '🏝️ Negeri Sembilan': 'nsembilan',
        '🏝️ Melaka': 'melaka',
        '🏝️ Johor': 'johor',
        '🌟 Stargazing Candidates': 'candidates'
    }
    selected_region = st.selectbox("Select Region", options=list(regions.keys()), index=0)
    region_key = regions[selected_region]
    
    region_map = {
        'perlis': PERLIS_LOCATIONS,
        'kedah': KEDAH_LOCATIONS,
        'penang': PENANG_LOCATIONS,
        'perak': PERAK_LOCATIONS,
        'kelantan': KELANTAN_LOCATIONS,
        'terengganu': TERENGGANU_LOCATIONS,
        'pahang': PAHANG_LOCATIONS,
        'selangor': SELANGOR_LOCATIONS,
        'kl': KUALA_LUMPUR_LOCATIONS,
        'nsembilan': NEGERI_SEMBILAN_LOCATIONS,
        'melaka': MELAKA_LOCATIONS,
        'johor': JOHOR_LOCATIONS,
        'candidates': STARGAZING_CANDIDATES,
    }
    
    if region_key == 'all':
        locations = WEST_MALAYSIA_LOCATIONS
        st.info(f"🌏 Showing {len(locations)} locations across West Malaysia")
    elif region_key == 'candidates':
        locations = STARGAZING_CANDIDATES
        st.info(f"🌟 Showing {len(locations)} stargazing candidates")
    else:
        locations = region_map.get(region_key, WEST_MALAYSIA_LOCATIONS)
        st.info(f"🏝️ {len(locations)} locations in {selected_region}")
    
    return locations, region_key


def render_haze_alert_card(haze: Dict):
    """Render haze OR fog alert card — v3.2.7 with validated ground-verified badge."""
    if not haze or not haze.get('detected'):
        return
    
    severity = haze.get('severity', 'None')
    is_fog = haze.get('is_fog', False)
    fog_type = haze.get('fog_type', None)
    ground_verified = haze.get('ground_verified', False)
    
    if is_fog:
        color = '#00f0ff'
        icon = '🌫️'
        if fog_type == 'tropical':
            fog_label = '🌴 TROPICAL HIGHLAND FOG'
            fog_desc = 'Warm humid highland cloud — common at Cameron, Genting, Fraser\'s Hill'
        elif fog_type == 'temperate':
            fog_label = '🏔️ MOUNTAIN FOG'
            fog_desc = 'Cold high-altitude cloud'
        else:
            fog_label = '🌫️ NATURAL FOG'
            fog_desc = 'High-altitude cloud'
        
        html_content = f'<div class="fog-alert recommendation-container" style="border: 2px solid {color}; background: {color}11; box-shadow: 0 0 30px {color}44;">'
        html_content += '<div style="display: flex; align-items: center; gap: 15px;">'
        html_content += f'<div style="font-size: 3rem;">{icon}</div>'
        html_content += '<div style="flex: 1;">'
        html_content += f'<div style="color: {color}; font-family: \'Courier New\', monospace; font-size: 1.3rem; font-weight: 900; letter-spacing: 2px;">{fog_label}</div>'
        html_content += f'<div style="color: #d0d0e8; font-family: \'Courier New\', monospace; font-size: 0.85rem; margin-top: 5px;">{fog_desc}</div>'
        html_content += f'<div style="color: #a0a0c0; font-family: \'Courier New\', monospace; font-size: 0.75rem; margin-top: 3px;">Confidence: {haze.get("confidence", "Unknown")} · {haze.get("cause", "Unknown cause")}</div>'
        html_content += '</div></div></div>'
        st.markdown(html_content, unsafe_allow_html=True)
        return
    
    colors = {
        'Severe': ('#ff2d95', '🚨'),
        'Heavy': ('#ff6600', '🔥'),
        'Moderate': ('#ffe84d', '⚠️'),
        'Light': ('#00f0ff', '💨'),
    }
    color, icon = colors.get(severity, ('#8080a0', 'ℹ️'))
    
    # Ground-verified badge text — only for validated stations
    verified_html = ''
    if ground_verified:
        station = haze.get('waqi_station', 'DOE station')
        dist = haze.get('waqi_station_distance_km')
        dist_note = f" · {dist:.0f}km" if dist is not None else ""
        verified_html = f'<span style="background: rgba(57, 255, 20, 0.15); color: #39ff14; padding: 2px 8px; border-radius: 4px; font-size: 0.65rem; margin-left: 8px;">✅ Ground-verified · {station}{dist_note}</span>'
    
    html_content = f'<div class="haze-alert recommendation-container" style="border: 2px solid {color}; background: {color}11; box-shadow: 0 0 30px {color}44;">'
    html_content += '<div style="display: flex; align-items: center; gap: 15px;">'
    html_content += f'<div style="font-size: 3rem;">{icon}</div>'
    html_content += '<div style="flex: 1;">'
    html_content += f'<div style="color: {color}; font-family: \'Courier New\', monospace; font-size: 1.3rem; font-weight: 900; letter-spacing: 2px;">HAZE ALERT: {severity.upper()}{verified_html}</div>'
    html_content += f'<div style="color: #d0d0e8; font-family: \'Courier New\', monospace; font-size: 0.85rem; margin-top: 5px;">Confidence: {haze.get("confidence", "Unknown")} · {haze.get("cause", "Unknown cause")}</div>'
    html_content += '</div></div></div>'
    st.markdown(html_content, unsafe_allow_html=True)


def render_air_quality_crosscheck(result_data: Dict):
    """
    V3.2.7: Show Open-Meteo vs WAQI side-by-side with distance validation info.
    """
    air_quality = result_data.get('air_quality')
    if not air_quality:
        return
    
    om_pm25 = air_quality.get('openmeteo_pm25')
    waqi_pm25 = air_quality.get('waqi_pm25')
    
    # Only show if we have at least one cross-check value
    if om_pm25 is None and waqi_pm25 is None:
        return
    
    with st.expander("🔬 Air Quality Cross-Check (Open-Meteo vs Ground Station)", expanded=False):
        st.caption("Open-Meteo uses CAMS model data which can lag real peaks. "
                   "WAQI mirrors DOE ground stations. The system uses the "
                   "**higher (more conservative) PM2.5** for safety. "
                   "WAQI stations >100 km away are automatically rejected.")
        
        cc1, cc2, cc3 = st.columns(3)
        
        with cc1:
            st.markdown("**📡 Open-Meteo CAMS**")
            if om_pm25 is not None:
                st.metric("PM2.5", f"{om_pm25:.1f} µg/m³")
            else:
                st.metric("PM2.5", "N/A")
            if air_quality.get('openmeteo_aqi') is not None:
                st.metric("US AQI", f"{air_quality['openmeteo_aqi']}")
        
        with cc2:
            st.markdown("**🏭 WAQI Ground Station**")
            if waqi_pm25 is not None:
                st.metric("PM2.5", f"{waqi_pm25:.1f} µg/m³")
            else:
                st.metric("PM2.5", "N/A")
            if air_quality.get('waqi_aqi') is not None:
                st.metric("US AQI", f"{air_quality['waqi_aqi']}")
            if air_quality.get('waqi_station'):
                dist = air_quality.get('waqi_station_distance_km')
                if dist is not None:
                    st.caption(f"📍 {air_quality['waqi_station']} · {dist:.1f} km away")
                else:
                    st.caption(f"📍 {air_quality['waqi_station']}")
        
        with cc3:
            st.markdown("**✅ Used (Higher)**")
            if air_quality.get('pm2_5') is not None:
                st.metric("PM2.5", f"{air_quality['pm2_5']:.1f} µg/m³")
            if air_quality.get('us_aqi') is not None:
                st.metric("US AQI", f"{air_quality['us_aqi']}")
            st.caption("Conservative value applied to haze detection")
        
        # Warning if ground station differs significantly
        if om_pm25 is not None and waqi_pm25 is not None:
            diff = waqi_pm25 - om_pm25
            if abs(diff) > 5:
                if diff > 0:
                    st.warning(f"⚠️ Ground station reads **{diff:.1f} µg/m³ HIGHER** than model — "
                               f"model may be underestimating haze event.")
                else:
                    st.info(f"ℹ️ Ground station reads **{abs(diff):.1f} µg/m³ LOWER** than model — "
                           f"haze may be dissipating faster than model predicts.")
        
        # V3.2.7: Note when WAQI was rejected (no nearby station)
        if waqi_pm25 is None and om_pm25 is not None:
            st.info("ℹ️ No nearby WAQI ground station available (<100 km). "
                    "Using Open-Meteo CAMS only.")


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <div style="font-size: 2.5rem; font-family: 'Courier New', monospace;
                 background: linear-gradient(90deg, #00f0ff, #b026ff, #ff2d95);
                 -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                 font-weight: 900; letter-spacing: 4px;">
                STARVIEW
            </div>
            <div style="color: #00f0ff; font-size: 0.8rem; font-family: 'Courier New', monospace;
                 letter-spacing: 6px;">
                WEST MALAYSIA · v3.2.7
            </div>
            <div class="cyber-divider"></div>
        </div>
        """, unsafe_allow_html=True)
        cache_stats = api_cache.get_stats()
        st.markdown(f"""
        <div style="color: #a0a0c0; font-family: 'Courier New', monospace; font-size: 0.7rem;
             text-align: center; border: 1px solid rgba(0, 240, 255, 0.1);
             border-radius: 4px; padding: 4px 8px; margin-bottom: 10px;">
            ⚡ CACHE: {cache_stats['total_cached']} RESPONSES
        </div>
        """, unsafe_allow_html=True)
        
        moon = calculate_moon_phase()
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; border: 1px solid rgba(0, 240, 255, 0.15);
             border-radius: 8px; background: rgba(0, 240, 255, 0.03); margin-bottom: 10px;">
            <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;
                 letter-spacing: 1px;">CURRENT MOON</div>
            <div style="font-size: 1.8rem;">{moon['emoji']}</div>
            <div style="color: #00f0ff; font-family: 'Courier New', monospace; font-size: 0.8rem;">
                {moon['phase_name']}
            </div>
            <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.65rem;">
                {moon['illumination_pct']}% illuminated
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        current_month = datetime.now().month
        seasonal = HAZE_SEASONAL_CALENDAR.get(current_month, HAZE_SEASONAL_CALENDAR[6])
        seasonal_risk, seasonal_source, seasonal_aqi, seasonal_note = seasonal
        
        risk_colors = {
            'Low': '#39ff14',
            'Low-Moderate': '#00f0ff',
            'Moderate': '#ffe84d',
            'High': '#ff6600',
            'Very High': '#ff2d95'
        }
        risk_color = risk_colors.get(seasonal_risk, '#8080a0')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 10px; border: 1px solid {risk_color}44;
             border-radius: 8px; background: {risk_color}11; margin-bottom: 10px;">
            <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;
                 letter-spacing: 1px;">HAZE SEASON</div>
            <div style="font-size: 1.5rem;">🌫️</div>
            <div style="color: {risk_color}; font-family: 'Courier New', monospace; font-size: 0.8rem;
                 font-weight: bold;">
                {seasonal_risk} Risk
            </div>
            <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;">
                AQI {seasonal_aqi}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.markdown('<div style="color:#00f0ff;font-family:Courier New,monospace;letter-spacing:2px;font-size:0.9rem;margin-bottom:10px;">⚡ LOCATION SELECTOR</div>', unsafe_allow_html=True)
        locations, region = render_region_selector()
        quick_location = st.selectbox("Select Location", list(locations.keys()), index=0)
        if st.button("⚡ GO TO LOCATION", use_container_width=True):
            coords = locations[quick_location]
            st.session_state.selected_location = Location(
                lat=coords[0], lon=coords[1], name=quick_location
            )
            st.rerun()
        st.caption("Or click on the map to select any location")
        st.divider()
        st.markdown('<div style="color:#00f0ff;font-family:Courier New,monospace;letter-spacing:2px;font-size:0.9rem;margin-bottom:10px;">🗺️ MAP SETTINGS</div>', unsafe_allow_html=True)
        basemap_choice = st.radio(
            "Map Style",
            options=["🗺️ OpenStreetMap", "🛰️ Satellite"],
            index=0 if st.session_state.basemap_choice == "OpenStreetMap" else 1,
            horizontal=True,
            label_visibility="collapsed"
        )
        st.session_state.basemap_choice = "Satellite" if "Satellite" in basemap_choice else "OpenStreetMap"
        st.session_state.show_radius_circle = st.checkbox("Show Search Radius", value=True)
        st.divider()
        st.markdown('<div style="color:#00f0ff;font-family:Courier New,monospace;letter-spacing:2px;font-size:0.9rem;margin-bottom:10px;">⚙️ ANALYSIS PARAMETERS</div>', unsafe_allow_html=True)
        radius = st.slider("Assessment Radius (m)", 2000, 20000, 10000, 1000)
        st.divider()
        st.markdown('<div style="color:#00f0ff;font-family:Courier New,monospace;letter-spacing:2px;font-size:0.9rem;margin-bottom:10px;">📊 SITE RANKING</div>', unsafe_allow_html=True)
        if st.session_state.current_results:
            result_data = st.session_state.current_results
            if 'suitability_percentage' in result_data:
                pct = result_data['suitability_percentage']
                rating = result_data['rating']
                color = "#39ff14" if pct >= 80 else "#00f0ff" if pct >= 65 else "#ff2d95" if pct >= 50 else "#ff6600"
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 1px solid rgba(0, 240, 255, 0.2);
                     border-radius: 8px; background: rgba(0, 240, 255, 0.05);">
                    <div style="font-size: 2.5rem; font-weight: 900; color: {color};
                         font-family: 'Courier New', monospace;">{pct}%</div>
                    <div style="color: #d0d0e8; font-family: 'Courier New', monospace;
                         letter-spacing: 2px; font-size: 0.8rem;">{rating}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Run an analysis to see site ranking")
        if st.button("🔄 COMPARE ALL", use_container_width=True):
            st.session_state.comparison_mode = True
            st.rerun()
        if st.button("🧹 CLEAR", use_container_width=True):
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.session_state.candidate_scores = {}
            st.rerun()
        if st.button("🗑️ CLEAR CACHE", use_container_width=True):
            api_cache.clear()
            st.success("Cache cleared!")
            st.rerun()
        st.divider()
        st.markdown('<div style="color:#00f0ff;font-family:Courier New,monospace;letter-spacing:2px;font-size:0.9rem;margin-bottom:10px;">🧠 AGENT MEMORY</div>', unsafe_allow_html=True)
        stats = st.session_state.agent.memory_repo.get_analysis_stats()
        col1, col2 = st.columns(2)
        with col1:
            st.metric("ANALYSES", stats['total_analyses'])
        with col2:
            st.metric("SUCCESS", f"{stats['success_rate']*100:.0f}%")
        if st.button("🗑️ CLEAR MEMORY", use_container_width=True):
            Path("starview_west_malaysia_memory.db").unlink(missing_ok=True)
            st.session_state.agent = StarViewWestMalaysiaAgent()
            st.session_state.analysis_history = []
            st.session_state.current_results = None
            st.session_state.reasoning_log = []
            st.rerun()
        return {'radius': radius}


def get_tiles_for_basemap(basemap_choice: str) -> str:
    if basemap_choice == "Satellite":
        return "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    return "OpenStreetMap"


def render_map(params: Dict):
    st.subheader("🗺️ West Malaysia Stargazing Site Map")
    center = [4.2, 102.0]
    location_name = "West Malaysia"
    if st.session_state.selected_location:
        center = [st.session_state.selected_location.lat, st.session_state.selected_location.lon]
        location_name = st.session_state.selected_location.name or "West Malaysia Location"

    basemap_choice = st.session_state.get('basemap_choice', 'OpenStreetMap')
    try:
        if basemap_choice == "Satellite":
            m = folium.Map(location=center, zoom_start=7,
                          tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                          attr='Esri World Imagery')
        else:
            m = folium.Map(location=center, zoom_start=7, tiles="OpenStreetMap")
    except Exception:
        m = folium.Map(location=center, zoom_start=7)

    for name, (lat, lon, radius_km, designation, desc) in PROTECTED_DARK_SKY_ZONES.items():
        folium.Circle(
            [lat, lon], radius=radius_km * 1000,
            color='#b026ff', fill=True, fillColor='#b026ff',
            fillOpacity=0.08, weight=1,
            tooltip=f"🏞️ {name} ({designation})"
        ).add_to(m)

    if st.session_state.selected_location:
        marker_color = 'purple'
        result_data = st.session_state.get('current_results', None)
        if result_data and 'suitability_percentage' in result_data:
            pct = result_data['suitability_percentage']
            if pct >= 80:
                marker_color = 'darkpurple'
            elif pct >= 65:
                marker_color = 'purple'
            elif pct >= 50:
                marker_color = 'blue'
            elif pct >= 35:
                marker_color = 'gray'
            else:
                marker_color = 'darkred'
        folium.Marker(
            center,
            popup=f"<b>🌟 {location_name}</b><br>Lat: {center[0]:.6f}<br>Lon: {center[1]:.6f}",
            tooltip="🌟 Stargazing Site",
            icon=folium.Icon(color=marker_color, icon='star', prefix='fa')
        ).add_to(m)
        if st.session_state.get('show_radius_circle', True):
            radius = params.get('radius', 10000)
            folium.Circle(center, radius=radius, color='#b026ff',
                         fill=True, fillColor='#b026ff', fillOpacity=0.1,
                         weight=2, tooltip=f"Radius: {radius}m").add_to(m)

    try:
        Fullscreen(position='topleft').add_to(m)
    except Exception:
        pass
    try:
        MiniMap(toggle_display=True, position='bottomright').add_to(m)
    except Exception:
        pass
    try:
        MousePosition(position='bottomleft', prefix='Coords: ').add_to(m)
    except Exception:
        pass

    map_data = st_folium(m, width=None, height=500, use_container_width=True)
    if map_data and map_data.get('last_clicked'):
        clicked_lat = map_data['last_clicked']['lat']
        clicked_lon = map_data['last_clicked']['lng']
        if st.session_state.selected_location is None or \
           abs(st.session_state.selected_location.lat - clicked_lat) > 0.0001 or \
           abs(st.session_state.selected_location.lon - clicked_lon) > 0.0001:
            st.session_state.selected_location = Location(lat=clicked_lat, lon=clicked_lon, name="West Malaysia Location")
            st.rerun()


def render_query_interface(params: Dict):
    st.subheader("💬 Natural Language Query")
    with st.expander("💡 Example Stargazing Queries", expanded=False):
        st.markdown("""
        **🌟 Stargazing Site Selection (West Malaysia):**
        - "Find the best stargazing spot in Pahang"
        - "Which location has the darkest skies in West Malaysia?"
        - "Where can I see the Milky Way clearly near KL?"

        **🌫️ Haze-Aware Queries:**
        - "Is there haze tonight at Cameron Highlands?"
        - "Check air quality at Genting Highlands"
        - "Is it safe for astrophotography tonight?"

        **📸 Astrophotography:**
        - "Best site for Milky Way photography in Peninsular Malaysia"
        - "Which location is best for deep-sky imaging in West Malaysia?"
        """)
    query = st.text_area(
        "Describe what you want to analyse for stargazing:",
        placeholder="e.g., Find the best stargazing spot in West Malaysia",
        height=100
    )
    col1, col2 = st.columns([1, 1])
    with col1:
        analyse_btn = st.button("🌟 ANALYSE SITE", type="primary", use_container_width=True)
    with col2:
        clear_btn = st.button("🧹 CLEAR", use_container_width=True)
    if clear_btn:
        st.session_state.current_results = None
        st.session_state.reasoning_log = []
        st.rerun()
    if analyse_btn and st.session_state.selected_location:
        with st.spinner("🌌 Analysing..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            def update_progress(progress, status):
                progress_bar.progress(progress)
                status_text.text(status)
            result = st.session_state.agent.execute_analysis(
                st.session_state.selected_location,
                query if query else "Evaluate this site for stargazing",
                params,
                progress_callback=update_progress
            )
            st.session_state.analysis_history.append(result)
            st.session_state.reasoning_log = result.steps
            st.session_state.current_results = result.final_result
            progress_bar.empty()
            status_text.empty()
            if result.success:
                st.success(f"✅ Analysis complete in {result.total_time:.2f}s")
                st.rerun()
            else:
                st.error("❌ Analysis failed. Check reasoning log.")
    elif analyse_btn:
        st.warning("Please select a location in West Malaysia first!")


def render_reasoning_log():
    st.subheader("🧠 Agent Reasoning")
    if not st.session_state.reasoning_log:
        st.info("Run a stargazing site analysis to see reasoning.")
        return
    for step in st.session_state.reasoning_log:
        status_icon = "✅" if step.status == "completed" else "❌" if step.status == "failed" else "⏳"
        with st.expander(f"{status_icon} Step {step.step_number}: {step.name}", expanded=False):
            st.write(f"**Reasoning:** {step.reasoning}")
            if step.execution_time > 0:
                st.write(f"**Execution Time:** {step.execution_time:.3f}s")


# ============================================================================
# EXPORT FUNCTIONALITY
# ============================================================================

def generate_export_csv(result_data: Dict) -> str:
    rows = []
    rows.append(['Category', 'Metric', 'Value'])
    rows.append(['Location', 'Name', result_data.get('location_name', 'Unknown')])
    rows.append(['Location', 'Latitude', result_data.get('lat', 0)])
    rows.append(['Location', 'Longitude', result_data.get('lon', 0)])
    rows.append(['Overall', 'Suitability %', result_data.get('suitability_percentage', 0)])
    rows.append(['Overall', 'Rating', result_data.get('rating', 'Unknown')])
    rows.append(['Overall', 'Recommendation', result_data.get('recommendation', '')])
    rows.append(['Overall', 'Base Score %', result_data.get('base_percentage', 0)])
    rows.append(['Overall', 'Penalty %', result_data.get('penalty_applied', 0)])
    
    pz = result_data.get('protected_zone')
    if pz:
        rows.append(['Protected Zone', 'Name', pz.get('name', '')])
        rows.append(['Protected Zone', 'Designation', pz.get('designation', '')])
        rows.append(['Protected Zone', 'Is Inside', pz.get('is_inside', False)])
        rows.append(['Protected Zone', 'Distance km', pz.get('distance_km', 0)])
    else:
        rows.append(['Protected Zone', 'Name', 'None'])
    
    haze = result_data.get('haze', {})
    rows.append(['Haze', 'Detected', haze.get('detected', False)])
    rows.append(['Haze', 'Is Fog', haze.get('is_fog', False)])
    rows.append(['Haze', 'Fog Type', haze.get('fog_type', 'N/A')])
    rows.append(['Haze', 'Severity', haze.get('severity', 'None')])
    rows.append(['Haze', 'Confidence', haze.get('confidence', 'N/A')])
    rows.append(['Haze', 'Cause', haze.get('cause', 'N/A')])
    rows.append(['Haze', 'Seasonal Risk', haze.get('seasonal_risk', 'N/A')])
    rows.append(['Haze', 'Ground Verified', haze.get('ground_verified', False)])
    rows.append(['Haze', 'WAQI Station', haze.get('waqi_station', 'N/A')])
    rows.append(['Haze', 'WAQI Station Distance km', haze.get('waqi_station_distance_km', 'N/A')])
    if haze.get('pm25'):
        rows.append(['Haze', 'PM2.5 (µg/m³) - Used', haze.get('pm25')])
    if haze.get('waqi_pm25'):
        rows.append(['Haze', 'PM2.5 (µg/m³) - WAQI', haze.get('waqi_pm25')])
    if haze.get('aqi'):
        rows.append(['Haze', 'AQI', haze.get('aqi')])
    if haze.get('health_advisory'):
        rows.append(['Haze', 'Health Advisory', haze.get('health_advisory')])
    
    # Air Quality cross-check details
    aq = result_data.get('air_quality')
    if aq:
        if aq.get('openmeteo_pm25') is not None:
            rows.append(['Air Quality', 'Open-Meteo PM2.5 (µg/m³)', aq.get('openmeteo_pm25')])
        if aq.get('waqi_pm25') is not None:
            rows.append(['Air Quality', 'WAQI PM2.5 (µg/m³)', aq.get('waqi_pm25')])
        if aq.get('waqi_station'):
            rows.append(['Air Quality', 'WAQI Station', aq.get('waqi_station')])
        if aq.get('waqi_station_distance_km') is not None:
            rows.append(['Air Quality', 'WAQI Station Distance km', aq.get('waqi_station_distance_km')])
        if aq.get('source'):
            rows.append(['Air Quality', 'Source', aq.get('source')])
    
    details = result_data.get('details', {})
    scores = result_data.get('scores', {})
    for key, detail in details.items():
        rows.append(['Score', key.replace('_', ' ').title(), f"{scores.get(key, 0):.2f}/5"])
        rows.append(['Score Value', key.replace('_', ' ').title(), str(detail.get('value', 'N/A'))])
        rows.append(['Score Weight', key.replace('_', ' ').title(), f"{detail.get('weight', 0)*100:.0f}%"])
        rows.append(['Score Source', key.replace('_', ' ').title(), str(detail.get('source', 'Unknown'))])
    
    w = result_data.get('weather')
    if w:
        rows.append(['Weather', 'Cloud Cover %', w.get('cloud_cover_pct', 'N/A')])
        rows.append(['Weather', 'Temperature °C', w.get('temperature_c', 'N/A')])
        rows.append(['Weather', 'Humidity %', w.get('humidity_pct', 'N/A')])
        rows.append(['Weather', 'Visibility km', w.get('visibility_km', 'N/A')])
        rows.append(['Weather', 'Wind m/s', w.get('wind_speed_ms', 'N/A')])
        rows.append(['Weather', 'Dew Point °C', w.get('dew_point_c', 'N/A')])
    
    moon = result_data.get('moon_phase')
    if moon:
        rows.append(['Moon', 'Phase', moon.get('phase_name', 'Unknown')])
        rows.append(['Moon', 'Illumination %', moon.get('illumination_pct', 0)])
        rows.append(['Moon', 'Impact', moon.get('impact', '')])
    
    mw = result_data.get('milky_way')
    if mw:
        rows.append(['Milky Way', 'Visibility', mw.get('visibility', '')])
        rows.append(['Milky Way', 'Best Time', mw.get('best_time', '')])
        rows.append(['Milky Way', 'Note', mw.get('note', '')])
    
    astro = result_data.get('astrophotography_scores')
    if astro:
        for mode, data in astro.items():
            rows.append(['Astro Score', mode.replace('_', ' ').title(), f"{data['score']}% ({data['rating']})"])
    
    df = pd.DataFrame(rows, columns=['Category', 'Metric', 'Value'])
    return df.to_csv(index=False)


def generate_export_json(result_data: Dict) -> str:
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'version': 'v3.2.7 West Malaysia',
        'location': {
            'name': result_data.get('location_name', 'Unknown'),
            'latitude': result_data.get('lat', 0),
            'longitude': result_data.get('lon', 0),
        },
        'overall': {
            'suitability_percentage': result_data.get('suitability_percentage', 0),
            'rating': result_data.get('rating', 'Unknown'),
            'recommendation': result_data.get('recommendation', ''),
            'base_percentage': result_data.get('base_percentage', 0),
            'penalty_applied': result_data.get('penalty_applied', 0),
            'penalty_reasons': result_data.get('penalty_reasons', []),
        },
        'protected_zone': result_data.get('protected_zone'),
        'haze': result_data.get('haze'),
        'air_quality': result_data.get('air_quality'),
        'scores': {k: round(v, 2) for k, v in result_data.get('scores', {}).items()},
        'details': {},
        'weather': result_data.get('weather'),
        'moon_phase': result_data.get('moon_phase'),
        'milky_way': result_data.get('milky_way'),
        'astrophotography_scores': result_data.get('astrophotography_scores'),
        'data_sources': result_data.get('data_source_details', []),
    }
    for key, detail in result_data.get('details', {}).items():
        export_data['details'][key] = {
            'score': detail.get('score', 0),
            'value': str(detail.get('value', 'N/A')),
            'weight': detail.get('weight', 0),
            'source': detail.get('source', 'Unknown'),
        }
    return json.dumps(export_data, indent=2, default=str)


def render_export_section(result_data: Dict):
    st.write("---")
    st.write("**📊 Export Report**")
    st.caption("Download the full analysis report (includes haze & air quality data).")
    
    location_name = result_data.get('location_name', 'West_Malaysia_Location')
    safe_name = "".join(c for c in location_name if c.isalnum() or c in (' ', '-', '_')).replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    
    col1, col2 = st.columns(2)
    with col1:
        csv_data = generate_export_csv(result_data)
        st.download_button(
            label="📥 Download CSV Report",
            data=csv_data,
            file_name=f"starview_{safe_name}_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col2:
        json_data = generate_export_json(result_data)
        st.download_button(
            label="📥 Download JSON Report",
            data=json_data,
            file_name=f"starview_{safe_name}_{timestamp}.json",
            mime="application/json",
            use_container_width=True,
        )


# ============================================================================
# RESULTS RENDERING
# ============================================================================

def render_results():
    st.subheader("🌟 Stargazing Site Analysis Results")
    if not st.session_state.analysis_history:
        st.info("No analysis results yet. Run a stargazing analysis.")
        return
    last_result = st.session_state.analysis_history[-1]
    if not last_result.final_result:
        st.warning("No results available.")
        return
    result_data = last_result.final_result
    if not result_data.get('success', False):
        st.error(f"Analysis failed: {result_data.get('error', 'Unknown error')}")
        return
    if 'suitability_percentage' in result_data:
        if result_data.get('protected_zone'):
            pz = result_data['protected_zone']
            if pz.get('is_inside'):
                st.success(f"🏞️ **Protected Dark-Sky Zone (INSIDE):** {pz['name']} ({pz['designation']})")
            else:
                st.info(f"🏞️ **Near Protected Zone:** {pz['name']} (~{pz.get('distance_km', 0):.1f} km away, {pz['designation']})")

        haze = result_data.get('haze', {})
        if haze.get('detected'):
            render_haze_alert_card(haze)

        if result_data.get('used_osm', False):
            st.success("🌐 **HYBRID v3.2.7 West Malaysia: WAQI-Distance-Validated + Peak Elevation + Tropical Fog + Haze**")
        else:
            st.success("📍 **Geographic Rules v3.2.7 West Malaysia (INSTANT)**")

        if haze.get('detected') or haze.get('aqi'):
            st.write("---")
            is_fog = haze.get('is_fog', False)
            fog_type = haze.get('fog_type', None)
            
            if is_fog:
                if fog_type == 'tropical':
                    st.write("**🌴 Tropical Highland Fog Analysis**")
                else:
                    st.write("**🏔️ Mountain Fog Analysis**")
            else:
                st.write("**🌫️ Haze & Air Quality Analysis**")
            
            hz1, hz2, hz3 = st.columns([1.2, 1, 1])
            
            with hz1:
                sev = haze.get('severity', 'None')
                if is_fog:
                    sev_colors = {'Fog': '#00f0ff'}
                    label_prefix = "FOG"
                    type_label = fog_type.upper() if fog_type else "NATURAL"
                else:
                    sev_colors = {
                        'Severe': '#ff2d95',
                        'Heavy': '#ff6600',
                        'Moderate': '#ffe84d',
                        'Light': '#00f0ff',
                        'None': '#39ff14',
                    }
                    label_prefix = "HAZE"
                    type_label = ""
                sev_color = sev_colors.get(sev, '#8080a0')
                
                card_html = f'<div style="text-align: center; padding: 15px; border: 1px solid {sev_color}66; border-radius: 10px; background: {sev_color}11;">'
                card_html += '<div style="font-size: 2rem;">🌫️</div>'
                card_html += f'<div style="color: {sev_color}; font-family: \'Courier New\', monospace; font-size: 0.9rem; font-weight: bold;">{label_prefix}: {sev.upper()}</div>'
                if type_label:
                    card_html += f'<div style="color: #a0a0c0; font-size: 0.65rem;">{type_label}</div>'
                if haze.get('ground_verified'):
                    card_html += f'<div style="color: #39ff14; font-size: 0.6rem;">✅ GROUND-VERIFIED</div>'
                card_html += f'<div style="color: #8080a0; font-family: \'Courier New\', monospace; font-size: 0.65rem; margin-top: 5px;">Confidence: {haze.get("confidence", "N/A")}</div>'
                card_html += '</div>'
                st.markdown(card_html, unsafe_allow_html=True)
            
            with hz2:
                if haze.get('pm25') is not None:
                    st.metric("PM2.5", f"{haze['pm25']:.1f} µg/m³")
                if haze.get('aqi') is not None:
                    st.metric("AQI", f"{haze['aqi']}")
            
            with hz3:
                if haze.get('pm10') is not None:
                    st.metric("PM10", f"{haze['pm10']:.1f} µg/m³")
                st.metric("Month Risk", haze.get('seasonal_risk', 'N/A'))
            
            if haze.get('health_advisory'):
                if is_fog:
                    st.success(haze['health_advisory'])
                else:
                    st.info(haze['health_advisory'])
            
            if haze.get('action_recommendation'):
                sev = haze.get('severity', 'None')
                if is_fog:
                    st.info(haze['action_recommendation'])
                elif sev in ['Heavy', 'Severe']:
                    st.error(haze['action_recommendation'])
                elif sev == 'Moderate':
                    st.warning(haze['action_recommendation'])
                else:
                    st.success(haze['action_recommendation'])
            
            # Air Quality Cross-Check card
            render_air_quality_crosscheck(result_data)
            
            if haze.get('indicators'):
                with st.expander("🔍 Detection Indicators"):
                    for ind in haze['indicators']:
                        st.write(f"• {ind}")

        moon = result_data.get('moon_phase')
        if moon:
            st.write("---")
            st.write("**🌙 Current Moon Phase**")
            moon_col1, moon_col2, moon_col3 = st.columns([1, 2, 2])
            with moon_col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 1px solid rgba(255, 232, 77, 0.3);
                     border-radius: 10px; background: rgba(255, 232, 77, 0.05);">
                    <div style="font-size: 3rem;">{moon['emoji']}</div>
                    <div style="color: #ffe84d; font-family: 'Courier New', monospace;
                         font-size: 0.9rem; font-weight: bold;">{moon['phase_name']}</div>
                </div>
                """, unsafe_allow_html=True)
            with moon_col2:
                st.metric("Illumination", f"{moon['illumination_pct']}%")
                st.metric("Moon Age", f"{moon['age_days']} days")
            with moon_col3:
                st.metric("Viewing Impact", moon['impact_emoji'])
                st.caption(f"**{moon['impact']}**")

        mw = result_data.get('milky_way')
        if mw:
            st.write("---")
            st.write("**🌌 Milky Way Visibility**")
            mw_col1, mw_col2, mw_col3 = st.columns([1, 2, 2])
            visibility_color = {
                'Peak': '#39ff14',
                'Excellent': '#00f0ff',
                'Good': '#ffe84d',
                'Limited': '#ff6600',
                'Poor': '#ff2d95'
            }.get(mw['visibility'], '#8080a0')
            with mw_col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 1px solid {visibility_color}66;
                     border-radius: 10px; background: {visibility_color}11;">
                    <div style="font-size: 2rem;">🌌</div>
                    <div style="color: {visibility_color}; font-family: 'Courier New', monospace;
                         font-size: 0.9rem; font-weight: bold;">{mw['visibility']}</div>
                </div>
                """, unsafe_allow_html=True)
            with mw_col2:
                st.metric("Best Viewing Time", mw['best_time'])
                st.metric("Latitude Position", mw['latitude_note'].split(' - ')[0])
            with mw_col3:
                st.info(f"📝 {mw['note']}")
                st.caption(f"**Next window:** {mw['next_window']}")

        astro = result_data.get('astrophotography_scores')
        if astro:
            st.write("---")
            st.write("**📸 Activity-Specific Scores**")
            st.caption("Different activities have different requirements.")
            
            ac1, ac2, ac3 = st.columns(3)
            with ac1:
                naked = astro['naked_eye']
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 1px solid rgba(0, 240, 255, 0.3);
                     border-radius: 10px; background: rgba(0, 240, 255, 0.05);">
                    <div style="font-size: 1.8rem;">👁️</div>
                    <div style="color: #00f0ff; font-family: 'Courier New', monospace;
                         font-size: 0.7rem; letter-spacing: 1px;">NAKED EYE</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #ffffff;
                         font-family: 'Courier New', monospace;">{naked['score']}%</div>
                    <div style="color: #ffe84d; font-family: 'Courier New', monospace;
                         font-size: 0.8rem;">{naked['emoji']} {naked['rating']}</div>
                    <div style="color: #8080a0; font-family: 'Courier New', monospace;
                         font-size: 0.65rem; margin-top: 5px;">{naked['note']}</div>
                </div>
                """, unsafe_allow_html=True)
            with ac2:
                tel = astro['telescope']
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 1px solid rgba(176, 38, 255, 0.3);
                     border-radius: 10px; background: rgba(176, 38, 255, 0.05);">
                    <div style="font-size: 1.8rem;">🔭</div>
                    <div style="color: #b026ff; font-family: 'Courier New', monospace;
                         font-size: 0.7rem; letter-spacing: 1px;">TELESCOPE</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #ffffff;
                         font-family: 'Courier New', monospace;">{tel['score']}%</div>
                    <div style="color: #ffe84d; font-family: 'Courier New', monospace;
                         font-size: 0.8rem;">{tel['emoji']} {tel['rating']}</div>
                    <div style="color: #8080a0; font-family: 'Courier New', monospace;
                         font-size: 0.65rem; margin-top: 5px;">{tel['note']}</div>
                </div>
                """, unsafe_allow_html=True)
            with ac3:
                photo = astro['astrophotography']
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; border: 1px solid rgba(255, 45, 149, 0.3);
                     border-radius: 10px; background: rgba(255, 45, 149, 0.05);">
                    <div style="font-size: 1.8rem;">📸</div>
                    <div style="color: #ff2d95; font-family: 'Courier New', monospace;
                         font-size: 0.7rem; letter-spacing: 1px;">ASTROPHOTOGRAPHY</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #ffffff;
                         font-family: 'Courier New', monospace;">{photo['score']}%</div>
                    <div style="color: #ffe84d; font-family: 'Courier New', monospace;
                         font-size: 0.8rem;">{photo['emoji']} {photo['rating']}</div>
                    <div style="color: #8080a0; font-family: 'Courier New', monospace;
                         font-size: 0.65rem; margin-top: 5px;">{photo['note']}</div>
                </div>
                """, unsafe_allow_html=True)

        st.write("---")
        if result_data.get('penalty_applied', 0) > 0:
            with st.expander(f"⚠️ Score Penalty: -{result_data['penalty_applied']}%"):
                st.write(f"**Base score:** {result_data.get('base_percentage', 0)}%")
                st.write(f"**Penalty:** -{result_data['penalty_applied']}%")
                st.write("**Reasons:**")
                for r in result_data.get('penalty_reasons', []):
                    st.warning(r)
                st.write(f"**Final score:** {result_data['suitability_percentage']}%")

        if 'data_source_details' in result_data:
            with st.expander("📊 Data Sources Used"):
                for detail in result_data['data_source_details']:
                    if '🏞️' in detail:
                        st.success(detail)
                    elif '🌫️' in detail:
                        st.warning(detail)
                    elif '🌐' in detail:
                        st.success(detail)
                    elif 'Air Quality' in detail:
                        st.info(f"💨 {detail}")
                    elif 'Cloud' in detail:
                        st.info(f"☁️ {detail}")
                    elif 'Light Pollution' in detail:
                        st.info(f"💡 {detail}")
                    elif 'Elevation' in detail:
                        st.info(f"⛰️ {detail}")
                    elif 'Curated' in detail or 'Peak' in detail:
                        st.success(f"✅ {detail}")
                    else:
                        st.info(f"📍 {detail}")

        weather = result_data.get('weather')
        if weather:
            with st.expander("🌤️ Live Weather (Open-Meteo)", expanded=False):
                wc1, wc2, wc3 = st.columns(3)
                with wc1:
                    if weather.get('cloud_cover_pct') is not None:
                        st.metric("☁️ Cloud Cover", f"{weather['cloud_cover_pct']:.0f}%",
                                  delta=weather.get('cloud_rating', ''))
                    if weather.get('temperature_c') is not None:
                        st.metric("🌡️ Temperature", f"{weather['temperature_c']:.1f}°C")
                with wc2:
                    if weather.get('humidity_pct') is not None:
                        st.metric("💧 Humidity", f"{weather['humidity_pct']:.0f}%")
                    if weather.get('visibility_km') is not None:
                        st.metric("👁️ Visibility", f"{weather['visibility_km']:.0f} km")
                with wc3:
                    if weather.get('dew_point_c') is not None:
                        st.metric("💦 Dew Point", f"{weather['dew_point_c']:.1f}°C")
                    if weather.get('wind_speed_ms') is not None:
                        st.metric("💨 Wind", f"{weather['wind_speed_ms']:.1f} m/s")
                if weather.get('cloud_explanation'):
                    st.caption(f"**Assessment:** {weather['cloud_explanation']}")

        if result_data.get('used_osm', False) and result_data.get('osm_data'):
            with st.expander("🌐 OSM Data Found"):
                st.json(result_data['osm_data'])

        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        with c1:
            st.metric("🌟 Stargazing Suitability", f"{result_data['suitability_percentage']}%",
                      delta=f"{result_data['rating']} {result_data['rating_emoji']}")
            st.caption(result_data['recommendation'])
        with c2:
            st.metric("Elevation", f"{result_data.get('elevation_m', 0):.0f}m")
        with c3:
            st.metric("Latitude", f"{result_data.get('lat_deg', 0):.1f}°N")
        with c4:
            cc = result_data.get('cloud_cover_pct')
            st.metric("☁️ Cloud", f"{cc:.0f}%" if cc is not None else "N/A")

        with st.expander("🔍 Why This Score? (Top Contributing Factors)", expanded=False):
            details = result_data.get('details', {})
            scores = result_data.get('scores', {})
            contributions = []
            for key, detail in details.items():
                w = detail.get('weight', 0)
                s = scores.get(key, 0)
                contributions.append({
                    'factor': key.replace('_', ' ').title(),
                    'score': s,
                    'weight': w,
                    'weighted': s * w,
                    'source': detail.get('source', 'Unknown')
                })
            contributions.sort(key=lambda x: x['weighted'], reverse=True)
            st.write("**Top positive contributors:**")
            for c in contributions[:3]:
                bar = "█" * int(c['weighted'] * 20)
                st.write(f"✅ **{c['factor']}** — Score: {c['score']:.1f}/5, Weight: {c['weight']*100:.0f}% — `{bar}` {c['weighted']:.2f}")
            st.write("**Lowest contributors:**")
            for c in contributions[-3:]:
                bar = "█" * int(c['weighted'] * 20)
                st.write(f"⚠️ **{c['factor']}** — Score: {c['score']:.1f}/5, Weight: {c['weight']*100:.0f}% — `{bar}` {c['weighted']:.2f}")

        st.write("---")
        st.write("**Detailed Scoring Breakdown:**")
        details = result_data.get('details', {})
        scores = result_data.get('scores', {})
        score_data = []
        for key, detail in details.items():
            weight = detail.get('weight', 0)
            score = scores.get(key, 0)
            weighted = score * weight
            source = detail.get('source', 'Unknown')
            if 'Protected' in source or '🏞️' in str(source):
                source_emoji = '🏞️'
            elif 'Curated' in source or 'Peak' in source:
                source_emoji = '✅'
            elif 'Geographic' in source:
                source_emoji = '📍'
            elif 'Live' in source:
                source_emoji = '✅'
            elif 'Open-Meteo' in source:
                source_emoji = '🌤️'
            elif 'Fallback' in source:
                source_emoji = '⚠️'
            else:
                source_emoji = 'ℹ️'
            score_data.append({
                'Criteria': key.replace('_', ' ').title(),
                'Score': f"{score:.1f}/5",
                'Value': detail.get('value', 'N/A'),
                'Weight': f"{weight*100:.0f}%",
                'Weighted': f"{weighted:.2f}",
                'Source': f"{source_emoji} {source[:40]}"
            })
        df = pd.DataFrame(score_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        chart_data = pd.DataFrame([
            {'Criteria': row['Criteria'], 'Score': float(row['Score'].split('/')[0])}
            for row in score_data
        ])
        st.bar_chart(chart_data.set_index('Criteria'))

        st.write("---")
        st.write("**📅 Best Viewing Season**")
        seasonal = get_seasonal_guidance(
            result_data.get('lat', 0),
            result_data.get('lon', 0),
            result_data.get('elevation_m', 0)
        )
        st.info(f"""
        **Region:** {seasonal['region']}

        🌟 **Best months:** {seasonal['best_months']}
        
        ✨ **Good months:** {seasonal['good_months']}
        
        ⚠️ **Avoid:** {seasonal['avoid_months']}
        
        📝 *{seasonal['notes']}*
        """)

        st.write("---")
        st.write("**🌫️ West Malaysia Haze Season Calendar**")
        current_m = datetime.now().month
        month_data = []
        for m in range(1, 13):
            risk, source, aqi, desc = HAZE_SEASONAL_CALENDAR[m]
            marker = " ⬅️ NOW" if m == current_m else ""
            month_data.append({
                'Month': datetime(2024, m, 1).strftime('%b'),
                'Haze Risk': risk,
                'Source': source,
                'Typical AQI': aqi,
                'Now': marker,
            })
        df_haze = pd.DataFrame(month_data)
        st.dataframe(df_haze, use_container_width=True, hide_index=True)
        
        current_seasonal = HAZE_SEASONAL_CALENDAR[current_m]
        st.caption(f"**Current month ({datetime(2024, current_m, 1).strftime('%B')}):** "
                   f"{current_seasonal[0]} haze risk — {current_seasonal[3]}")

        st.write("---")
        st.write("**📋 Detailed Recommendation Strategy**")
        recommendations = generate_recommendation_strategy(result_data)

        risk = recommendations.get('risk_level', 'Unknown')
        risk_color = ('#ff2d95' if risk in ('High', 'Very High')
                      else '#39ff14' if risk == 'Low' else '#ffe84d')

        st.markdown(f"""
        <div class="recommendation-container">
            <div class="recommendation-title">🎯 Overall Feasibility</div>
            <div style="color: #ffffff; font-family: 'Courier New', monospace; font-size: 1.1rem; padding: 10px;">
                {recommendations.get('overall_feasibility', 'Assessment not available')}
            </div>
            <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.8rem; border: 1px solid rgba(0,240,255,0.1); padding: 8px 15px; border-radius: 8px;">
                    💰 Investment: <span style="color: #00f0ff; font-weight: bold;">{recommendations.get('investment_required', 'Unknown')}</span>
                </div>
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.8rem; border: 1px solid rgba(255,45,149,0.3); padding: 8px 15px; border-radius: 8px;">
                    ⚠️ Risk: <span style="color: {risk_color}; font-weight: bold;">{risk}</span>
                </div>
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.8rem; border: 1px solid rgba(255,45,149,0.3); padding: 8px 15px; border-radius: 8px;">
                    🚨 Critical: <span style="color: #ff2d95; font-weight: bold;">{recommendations.get('critical_action_count', 0)}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if recommendations['immediate_actions']:
            st.markdown('<div class="recommendation-container"><div class="recommendation-title">🔴 IMMEDIATE ACTIONS (0-6 Months)</div>', unsafe_allow_html=True)
            for action in recommendations['immediate_actions']:
                st.markdown(f"""
                <div class="recommendation-item">
                    <span class="icon">{action.get('priority', '')}</span>
                    {action['text']}
                    <span style="float: right; color: #8080a0; font-size: 0.8rem;">{action.get('cost', '')}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if recommendations['short_term_actions']:
            st.markdown('<div class="recommendation-container"><div class="recommendation-title">🟡 SHORT-TERM ACTIONS (6-18 Months)</div>', unsafe_allow_html=True)
            for action in recommendations['short_term_actions']:
                st.markdown(f"""
                <div class="recommendation-item">
                    <span class="icon">{action.get('priority', '')}</span>
                    {action['text']}
                    <span style="float: right; color: #8080a0; font-size: 0.8rem;">{action.get('cost', '')}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        if recommendations['long_term_actions']:
            st.markdown('<div class="recommendation-container"><div class="recommendation-title">🟢 LONG-TERM ACTIONS (18-36 Months)</div>', unsafe_allow_html=True)
            for action in recommendations['long_term_actions']:
                st.markdown(f"""
                <div class="recommendation-item">
                    <span class="icon">{action.get('priority', '')}</span>
                    {action['text']}
                    <span style="float: right; color: #8080a0; font-size: 0.8rem;">{action.get('cost', '')}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        render_export_section(result_data)


def render_comparison_mode():
    st.subheader("🔄 Stargazing Site Comparison Dashboard")
    with st.spinner("Analysing all candidate sites..."):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        for i, (name, coords) in enumerate(STARGAZING_CANDIDATES.items()):
            status_text.text(f"Analysing: {name}")
            progress_bar.progress((i + 1) / len(STARGAZING_CANDIDATES))
            location = Location(lat=coords[0], lon=coords[1], name=name)
            params = {'radius': 10000}
            try:
                strategy = StrategySelector.get_strategy('stargazing')
                result = strategy.analyse(location, params)
                if result.get('success'):
                    moon = calculate_moon_phase()
                    astro = calculate_astrophotography_scores(result, moon)
                    mw = get_milky_way_visibility(coords[0], coords[1])
                    haze = result.get('haze', {})
                    is_fog = haze.get('is_fog', False)
                    fog_type = haze.get('fog_type', None)
                    if is_fog:
                        if fog_type == 'tropical':
                            haze_label = '🌴 Tropical Fog'
                        else:
                            haze_label = '🏔️ Fog'
                    else:
                        haze_label = haze.get('severity', 'None')
                    results.append({
                        'Site': name,
                        'Suitability %': result['suitability_percentage'],
                        'Rating': result['rating'],
                        'Elevation (m)': result.get('elevation_m', 0),
                        'Light Pollution': result.get('light_pollution_index', 0),
                        'Cloud Risk': result.get('cloud_risk', 'Unknown'),
                        'Haze': haze_label,
                        'AstroPhoto %': astro['astrophotography']['score'],
                        'Protected': '🏞️' if result.get('protected_zone') else '',
                    })
            except Exception as e:
                results.append({
                    'Site': name, 'Suitability %': 0, 'Rating': 'Error',
                    'Elevation (m)': 0, 'Light Pollution': 0, 'Cloud Risk': 'Unknown',
                    'Haze': 'N/A', 'AstroPhoto %': 0, 'Protected': '',
                })
        progress_bar.empty()
        status_text.empty()
        if results:
            df = pd.DataFrame(results)
            df_sorted = df.sort_values('Suitability %', ascending=False)
            st.write(f"**📊 Comparison of {len(results)} Sites**")
            top_site = df_sorted.iloc[0]
            st.success(f"🌟 **Top Recommended: {top_site['Site']}** ({top_site['Suitability %']:.1f}%)")
            display_cols = ['Site', 'Suitability %', 'Rating', 'Elevation (m)', 'Light Pollution', 'Haze', 'Cloud Risk', 'AstroPhoto %', 'Protected']
            st.dataframe(df_sorted[display_cols], use_container_width=True, hide_index=True)
            chart_data = df_sorted[['Site', 'Suitability %']].set_index('Site')
            st.bar_chart(chart_data)

            basemap_choice = st.session_state.get('basemap_choice', 'OpenStreetMap')
            if basemap_choice == "Satellite":
                m = folium.Map(location=[4.2, 102.0], zoom_start=7,
                              tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                              attr='Esri World Imagery')
            else:
                m = folium.Map(location=[4.2, 102.0], zoom_start=7, tiles="OpenStreetMap")

            for _, row in df.iterrows():
                score = row['Suitability %']
                if score >= 80:
                    color = 'darkpurple'
                elif score >= 65:
                    color = 'purple'
                elif score >= 50:
                    color = 'blue'
                elif score >= 35:
                    color = 'gray'
                else:
                    color = 'darkred'
                coords = STARGAZING_CANDIDATES.get(row['Site'], (0, 0))
                folium.Marker(
                    coords,
                    popup=f"<b>{row['Site']}</b><br>Score: {score:.1f}%<br>Rating: {row['Rating']}<br>Haze: {row['Haze']}<br>AstroPhoto: {row['AstroPhoto %']}%",
                    tooltip=f"{row['Site']}: {score:.1f}%",
                    icon=folium.Icon(color=color, icon='star', prefix='fa')
                ).add_to(m)
            try:
                Fullscreen(position='topleft').add_to(m)
            except Exception:
                pass
            st_folium(m, width=None, height=400, use_container_width=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            st.download_button(
                label="📥 Download Comparison CSV",
                data=df_sorted[display_cols].to_csv(index=False),
                file_name=f"starview_comparison_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True,
            )

            selected_site = st.selectbox("Select a site for detailed analysis:", df_sorted['Site'].tolist())
            if selected_site:
                coords = STARGAZING_CANDIDATES[selected_site]
                st.session_state.selected_location = Location(
                    lat=coords[0], lon=coords[1], name=selected_site
                )
                st.session_state.comparison_mode = False
                st.rerun()


def render_memory_explorer():
    st.subheader("💾 Memory Explorer")
    tab1, tab2 = st.tabs(["Past Analyses", "Learned Parameters"])
    with tab1:
        all_analyses = st.session_state.agent.memory_repo.get_all_analyses(limit=20)
        if all_analyses:
            st.write(f"**{len(all_analyses)} past analyses**")
            for entry in all_analyses:
                query_preview = entry['query'][:50] + "..." if len(entry['query']) > 50 else entry['query']
                with st.expander(f"{'✅' if entry['success'] else '❌'} {query_preview}", expanded=False):
                    st.write(f"**Query:** {entry['query']}")
                    st.write(f"**Time:** {entry['execution_time']:.2f}s")
                    st.write(f"**Timestamp:** {entry['timestamp']}")
        else:
            st.info("No past analyses yet.")
    with tab2:
        try:
            conn = sqlite3.connect("starview_west_malaysia_memory.db")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM learned_parameters ORDER BY success_rate DESC")
            rows = cursor.fetchall()
            conn.close()
            if rows:
                df = pd.DataFrame(rows, columns=['ID', 'Analysis Type', 'Parameter', 'Value', 'Success Rate', 'Usage Count', 'Last Updated'])
                st.dataframe(df[['Analysis Type', 'Parameter', 'Value', 'Success Rate', 'Usage Count']], use_container_width=True)
            else:
                st.info("No learned parameters yet.")
        except Exception:
            st.info("No learned parameters yet.")


def main():
    st.set_page_config(page_title="StarView West Malaysia", page_icon="🌌", layout="wide")
    st.markdown(CYBERPUNK_CSS, unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align: center; padding: 20px 0 10px 0;">
        <div class="main-title">🌌 STARVIEW</div>
        <div class="subtitle">PENINSULAR MALAYSIA · STARGAZING SITE SELECTOR v3.2.7</div>
        <div class="cyber-divider"></div>
        <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem;
             letter-spacing: 4px; margin-top: 5px;">
            🌫️ FOG DETECTION · 💨 WAQI-DISTANCE-VALIDATED · 🏞️ PROTECTED ZONES · 🌙 MOON · 🌌 MILKY WAY · 📊 EXPORT
        </div>
    </div>
    """, unsafe_allow_html=True)
    init_session_state()
    total_locations = len(WEST_MALAYSIA_LOCATIONS)
    st.markdown(f"""
    <div style="display: flex; justify-content: space-between; padding: 8px 15px;
         border: 1px solid rgba(0, 240, 255, 0.1); border-radius: 8px;
         background: rgba(0, 240, 255, 0.03); margin-bottom: 15px; flex-wrap: wrap; gap: 10px;">
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem;">
            📍 LOCATIONS: <span style="color: #00f0ff; font-weight: bold;">{total_locations}</span>
        </span>
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem;">
            🏞️ PROTECTED: <span style="color: #b026ff; font-weight: bold;">{len(PROTECTED_DARK_SKY_ZONES)}</span>
        </span>
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem;">
            🌟 CANDIDATES: <span style="color: #39ff14; font-weight: bold;">{len(STARGAZING_CANDIDATES)}</span>
        </span>
        <span style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.7rem;">
            ✅ NEW: <span style="color: #00f0ff; font-weight: bold;">v3.2.7 WAQI Distance Validation</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('comparison_mode', False):
        render_comparison_mode()
        if st.button("← BACK TO SINGLE SITE"):
            st.session_state.comparison_mode = False
            st.rerun()
        return

    params = render_sidebar()
    col1, col2 = st.columns([1.5, 1])
    with col1:
        render_map(params)
        render_query_interface(params)
    with col2:
        if st.session_state.selected_location:
            name = st.session_state.selected_location.name or "West Malaysia Location"
            st.markdown(f"""
            <div style="padding: 10px 15px; border: 1px solid rgba(0, 240, 255, 0.15);
                 border-radius: 8px; background: rgba(0, 240, 255, 0.03); margin-bottom: 15px;">
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;">
                    SELECTED LOCATION</div>
                <div style="color: #00f0ff; font-family: 'Courier New', monospace; font-size: 0.9rem;">
                    {name}</div>
                <div style="color: #8080a0; font-family: 'Courier New', monospace; font-size: 0.6rem;">
                    {st.session_state.selected_location.lat:.4f}, {st.session_state.selected_location.lon:.4f}</div>
            </div>
            """, unsafe_allow_html=True)
        render_reasoning_log()
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        render_results()
    with col2:
        render_memory_explorer()
    st.markdown("""
    <div class="cyber-divider"></div>
    <div style="text-align: center; padding: 15px 0; color: #333; font-family: 'Courier New', monospace;
         font-size: 0.6rem; letter-spacing: 2px;">
        <span style="color: #00f0ff;">[</span>
        STARVIEW WEST MALAYSIA v3.2.7 · WAQI-DISTANCE-VALIDATED + PEAK ELEVATION + INSIDE/NEAR PROTECTED ZONES
        <span style="color: #00f0ff;">]</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()