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
    /* Only apply to main content area, not sidebar */
    .main div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMarkdownContainer"]) {
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
    
    .main div[data-testid="stVerticalBlock"] > div:has(div[data-testid="stMarkdownContainer"]):hover {
        background: var(--bg-glass-hover);
        border-color: rgba(59, 130, 246, 0.3);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px 0 rgba(59, 130, 246, 0.2);
    }
    
    /* ===== SIDEBAR STYLING ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(10, 15, 26, 0.95) 0%, rgba(26, 31, 46, 0.95) 100%) !important;
        border-right: 1px solid var(--border-glass);
    }
    
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
        overflow-y: auto !important;
    }
    
    /* Ensure sidebar content is scrollable and interactive */
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        overflow-y: auto !important;
        pointer-events: auto !important;
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
        padding: 0.75rem 1rem !important;
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
    
    /* ===== COMPLETELY HIDE KEYBOARD ARROW TEXT ===== */
    /* Target ALL possible selectors for the Material Icons text */
    .material-symbols-rounded,
    [class*="material-symbols"],
    span[class*="st-emotion-cache"]:not([data-testid]),
    [data-testid="stSidebarCollapseButton"] span,
    [data-testid="stExpanderToggleIcon"] span,
    button[kind="header"] span,
    section[data-testid="stSidebar"] button span {
        font-size: 0 !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
        overflow: hidden !important;
        display: none !important;
        color: transparent !important;
        -webkit-text-fill-color: transparent !important;
    }
    
    /* Sidebar collapse button styling */
    [data-testid="stSidebarCollapseButton"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-width: auto !important;
    }
    
    /* When sidebar is OPEN - show close arrow */
    section[data-testid="stSidebar"][aria-expanded="true"] [data-testid="stSidebarCollapseButton"]::after {
        content: "◀ Close" !important;
        font-size: 12px !important;
        font-family: 'Inter', sans-serif !important;
        color: white !important;
        font-weight: 500 !important;
        display: block !important;
        visibility: visible !important;
    }
    
    /* When sidebar is COLLAPSED - show expand message */
    section[data-testid="stSidebar"][aria-expanded="false"] [data-testid="stSidebarCollapseButton"]::after,
    [data-testid="stSidebarCollapseButton"]::after {
        content: "Click to expand to select Data sources" !important;
        font-size: 11px !important;
        font-family: 'Inter', sans-serif !important;
        color: white !important;
        font-weight: 500 !important;
        display: block !important;
        visibility: visible !important;
        white-space: nowrap !important;
    }
    
    /* Hide the text that says keyboard_double_arrow using font-face override */
    @font-face {
        font-family: 'Material Symbols Rounded';
        src: local('Arial');
        unicode-range: U+0000-00FF;
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
    /* Only apply to main content columns, not sidebar */
    .main div[data-testid="column"] {
        background: var(--bg-glass);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-glass);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.25rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }
    
    /* Sidebar columns should be simple */
    section[data-testid="stSidebar"] div[data-testid="column"] {
        background: transparent;
        backdrop-filter: none;
        border: none;
        border-radius: 0;
        padding: 0.25rem;
        margin: 0;
        box-shadow: none;
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
    
    /* ===== MOBILE SIDEBAR ENHANCEMENTS - PURE CSS ===== */
    /* CSS Checkbox Hack for Mobile Sidebar */
    @media (max-width: 768px) {
        /* Hidden checkbox to control sidebar state */
        #mobile-sidebar-toggle {
            display: none;
        }
        
        /* Mobile menu button */
        .mobile-menu-btn {
            display: block !important;
            position: fixed !important;
            top: 10px !important;
            left: 10px !important;
            z-index: 1000000 !important;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
            border: none !important;
            border-radius: 10px !important;
            padding: 12px !important;
            cursor: pointer !important;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.5) !important;
            transition: all 0.3s ease !important;
        }
        
        .mobile-menu-btn:hover {
            transform: scale(1.1) !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.7) !important;
        }
        
        .mobile-menu-btn svg {
            width: 24px !important;
            height: 24px !important;
            fill: white !important;
        }
        
        /* Sidebar positioning */
        section[data-testid="stSidebar"] {
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 280px !important;
            height: 100vh !important;
            z-index: 999999 !important;
            transform: translateX(-100%) !important;
            transition: transform 0.3s ease !important;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.3) !important;
        }
        
        /* Show sidebar when checkbox is checked */
        #mobile-sidebar-toggle:checked ~ .stApp section[data-testid="stSidebar"],
        #mobile-sidebar-toggle:checked ~ div section[data-testid="stSidebar"] {
            transform: translateX(0) !important;
        }
        
        /* Overlay when sidebar is open */
        #mobile-sidebar-toggle:checked ~ .stApp::before,
        #mobile-sidebar-toggle:checked ~ div::before {
            content: "" !important;
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            background: rgba(0, 0, 0, 0.5) !important;
            z-index: 999998 !important;
        }
        
        /* Hide default Streamlit toggle on mobile */
        button[data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        
        /* Adjust main content */
        section[data-testid="stSidebar"] ~ .main {
            margin-left: 0 !important;
        }
    }
    
    /* ===== DESKTOP SIDEBAR TOGGLE ===== */
    button[data-testid="stSidebarCollapseButton"] {
        visibility: visible !important;
        opacity: 1 !important;
        pointer-events: auto !important;
        z-index: 999999 !important;
        background: linear-gradient(135deg, var(--accent-blue) 0%, var(--accent-purple) 100%) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 8px !important;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4) !important;
        cursor: pointer !important;
    }
    
    button[data-testid="stSidebarCollapseButton"]:hover {
        transform: scale(1.1) !important;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6) !important;
    }
    
    /* Ensure header area doesn't block the toggle */
    header[data-testid="stHeader"] {
        background: transparent !important;
        pointer-events: none !important;
    }
    
    header[data-testid="stHeader"] * {
        pointer-events: auto !important;
    }
    
    </style>
    """
