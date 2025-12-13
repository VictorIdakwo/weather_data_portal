"""
Glassmorphism Dark Theme for Weather Data Portal
Professional dark mode design with glass effect cards
"""

def get_glassmorphism_css():
    """
    Returns custom CSS for glassmorphism dark theme.
    """
    return """
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* ===== ROOT VARIABLES ===== */
    :root {
        --bg-primary: #0a0f1a;
        --bg-glass: rgba(255, 255, 255, 0.03);
        --bg-glass-hover: rgba(255, 255, 255, 0.06);
        --text-primary: #ffffff;
        --text-secondary: #9ca3af;
        --accent-blue: #3b82f6;
        --accent-purple: #8b5cf6;
        --success: #22c55e;
        --warning: #eab308;
        --danger: #ef4444;
        --border-glass: rgba(255, 255, 255, 0.1);
    }
    
    /* ===== GLOBAL STYLES ===== */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    
    /* Main app background */
    .stApp {
        background: linear-gradient(135deg, #0a0f1a 0%, #1a1f2e 100%) !important;
        background-attachment: fixed;
    }
    
    /* Remove default Streamlit padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }
    
    /* ===== GLASSMORPHISM CARDS ===== */
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMarkdownContainer"]) {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s ease;
    }
    
    div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMarkdownContainer"]):hover {
        background: var(--bg-glass-hover);
        border-color: rgba(59, 130, 246, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(59, 130, 246, 0.2);
    }
    
    /* ===== SIDEBAR STYLING ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 15, 26, 0.95) 0%, rgba(26, 31, 46, 0.95) 100%) !important;
        backdrop-filter: blur(20px);
        border-right: 1px solid var(--border-glass);
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
    }
    
    /* Sidebar headers */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    
    /* ===== HEADERS ===== */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }
    
    h1 {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem !important;
    }
    
    h2 {
        color: var(--accent-blue) !important;
        font-size: 1.8rem !important;
    }
    
    h3 {
        font-size: 1.4rem !important;
    }
    
    /* ===== TEXT ===== */
    /* Default text colors - use lower specificity to allow overrides */
    p:not([style*="color"]), 
    span:not([style*="color"]), 
    label:not([style*="color"]), 
    div:not([style*="color"]) {
        color: var(--text-secondary);
    }
    
    strong:not([style*="color"]), 
    b:not([style*="color"]) {
        color: var(--text-primary);
        font-weight: 600;
    }
    
    /* Force footer section to use black text */
    div[style*="background-color: #f0f2f6"] * {
        color: #000000 !important;
    }
    
    div[style*="background-color: #f0f2f6"] a {
        color: #3b82f6 !important;
    }
    
    /* ===== BUTTONS ===== */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%) !important;
        color: var(--text-primary) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.3) !important;
        letter-spacing: 0.02em;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 30px rgba(59, 130, 246, 0.5) !important;
    }
    
    .stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* ===== INPUT FIELDS ===== */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-glass) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stMultiSelect > div > div:focus-within,
    .stDateInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Multi-select tags */
    .stMultiSelect span[data-baseweb="tag"] {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%) !important;
        border: none !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
        padding: 0.25rem 0.75rem !important;
    }
    
    /* ===== RADIO BUTTONS ===== */
    .stRadio > div {
        background: var(--bg-glass);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 1rem;
    }
    
    .stRadio > div > label > div[role="radiogroup"] > label {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
        margin: 0.25rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stRadio > div > label > div[role="radiogroup"] > label:hover {
        background: var(--bg-glass-hover) !important;
        border-color: var(--accent-blue) !important;
    }
    
    /* ===== CHECKBOXES ===== */
    .stCheckbox {
        color: var(--text-primary) !important;
    }
    
    .stCheckbox > label > div[role="checkbox"] {
        background: var(--bg-glass) !important;
        border: 1px solid var(--border-glass) !important;
        border-radius: 4px !important;
    }
    
    .stCheckbox > label > div[role="checkbox"][aria-checked="true"] {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%) !important;
        border-color: var(--accent-blue) !important;
    }
    
    /* ===== EXPANDERS ===== */
    .streamlit-expanderHeader {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-glass) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--bg-glass-hover) !important;
        border-color: var(--accent-blue) !important;
    }
    
    .streamlit-expanderContent {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-glass) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 0.75rem !important;
    }
    
    /* Just accept the keyboard text and style expanders nicely */
    .streamlit-expanderHeader {
        padding: 0.75rem 1rem !important;
    }
    
    /* ===== DATAFRAMES / TABLES ===== */
    .stDataFrame {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-glass) !important;
        border-radius: 12px !important;
        overflow: hidden;
    }
    
    .stDataFrame thead tr th {
        background: rgba(59, 130, 246, 0.1) !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        border-bottom: 2px solid var(--accent-blue) !important;
    }
    
    .stDataFrame tbody tr {
        background: var(--bg-glass) !important;
        border-bottom: 1px solid var(--border-glass) !important;
        transition: all 0.2s ease !important;
    }
    
    .stDataFrame tbody tr:hover {
        background: var(--bg-glass-hover) !important;
    }
    
    .stDataFrame td {
        color: var(--text-secondary) !important;
    }
    
    /* ===== ALERTS / MESSAGES ===== */
    .stSuccess {
        background: rgba(34, 197, 94, 0.1) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(34, 197, 94, 0.3) !important;
        border-left: 4px solid var(--success) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    .stInfo {
        background: rgba(59, 130, 246, 0.1) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(59, 130, 246, 0.3) !important;
        border-left: 4px solid var(--accent-blue) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    .stWarning {
        background: rgba(234, 179, 8, 0.1) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(234, 179, 8, 0.3) !important;
        border-left: 4px solid var(--warning) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    .stError {
        background: rgba(239, 68, 68, 0.1) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
        border-left: 4px solid var(--danger) !important;
        border-radius: 12px !important;
        color: var(--text-primary) !important;
    }
    
    /* ===== PROGRESS BAR ===== */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-blue) 0%, var(--accent-purple) 100%) !important;
        border-radius: 10px !important;
    }
    
    .stProgress > div > div {
        background: var(--bg-glass) !important;
        border-radius: 10px !important;
    }
    
    /* ===== SPINNER ===== */
    .stSpinner > div {
        border-top-color: var(--accent-blue) !important;
    }
    
    /* ===== METRICS ===== */
    div[data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
    }
    
    div[data-testid="stMetricDelta"] {
        color: var(--success) !important;
    }
    
    /* ===== FILE UPLOADER ===== */
    .stFileUploader {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px);
        border: 2px dashed var(--border-glass) !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader:hover {
        border-color: var(--accent-blue) !important;
        background: var(--bg-glass-hover) !important;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px);
        border-radius: 12px !important;
        padding: 0.5rem !important;
        gap: 0.5rem !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border: 1px solid transparent !important;
        border-radius: 8px !important;
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: var(--bg-glass-hover) !important;
        border-color: var(--border-glass) !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%) !important;
        border-color: var(--accent-blue) !important;
        color: var(--text-primary) !important;
    }
    
    /* ===== COLUMNS ===== */
    div[data-testid="column"] {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.25rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg-glass);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%);
    }
    
    /* ===== PLOTLY CHARTS ===== */
    .js-plotly-plot {
        background: var(--bg-glass) !important;
        backdrop-filter: blur(10px);
        border: 1px solid var(--border-glass) !important;
        border-radius: 16px !important;
        padding: 1rem !important;
    }
    
    /* ===== CUSTOM ANIMATIONS ===== */
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .stApp > div {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* ===== GLOW EFFECTS ===== */
    .glow-blue {
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.5),
                    0 0 40px rgba(59, 130, 246, 0.3),
                    0 0 60px rgba(59, 130, 246, 0.1);
    }
    
    .glow-purple {
        box-shadow: 0 0 20px rgba(139, 92, 246, 0.5),
                    0 0 40px rgba(139, 92, 246, 0.3),
                    0 0 60px rgba(139, 92, 246, 0.1);
    }
    
    /* ===== HIDE STREAMLIT BRANDING ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    </style>
    """
