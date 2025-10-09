from typing import Dict, List, Tuple

# Nigeria States and FCT with approximate centroids (lat, lon)
NIGERIA_STATES = {
    "Abia": (5.4527, 7.5248),
    "Adamawa": (9.3265, 12.3984),
    "Akwa Ibom": (5.0077, 7.8500),
    "Anambra": (6.2209, 6.9370),
    "Bauchi": (10.7697, 9.9988),
    "Bayelsa": (4.7719, 6.0699),
    "Benue": (7.3347, 8.7403),
    "Borno": (11.8333, 13.1500),
    "Cross River": (5.8734, 8.5980),
    "Delta": (5.6808, 6.0185),
    "Ebonyi": (6.2649, 8.0137),
    "Edo": (6.6346, 5.9157),
    "Ekiti": (7.7190, 5.3110),
    "Enugu": (6.5354, 7.4381),
    "FCT": (9.0765, 7.3986),  # Federal Capital Territory (Abuja)
    "Gombe": (10.2904, 11.1670),
    "Imo": (5.5720, 7.0588),
    "Jigawa": (12.2289, 9.5619),
    "Kaduna": (10.5265, 7.4388),
    "Kano": (12.0022, 8.5919),
    "Katsina": (12.9908, 7.6177),
    "Kebbi": (11.4969, 4.1975),
    "Kogi": (7.7327, 6.6936),
    "Kwara": (8.9668, 4.3866),
    "Lagos": (6.5244, 3.3792),
    "Nasarawa": (8.5377, 8.5119),
    "Niger": (9.9315, 5.5980),
    "Ogun": (6.9969, 3.4700),
    "Ondo": (6.9149, 5.1478),
    "Osun": (7.5629, 4.5200),
    "Oyo": (8.1572, 3.6161),
    "Plateau": (9.2182, 9.5179),
    "Rivers": (4.8396, 6.9112),
    "Sokoto": (13.0622, 5.2430),
    "Taraba": (7.9993, 10.7739),
    "Yobe": (12.2939, 11.9660),
    "Zamfara": (12.1219, 6.2200),
}

# Major LGAs for selected states (this is a subset - full list would be very large)
# Format: {"State": {"LGA": (lat, lon)}}
NIGERIA_LGAS = {
    "Lagos": {
        "Agege": (6.6180, 3.3168),
        "Ajeromi-Ifelodun": (6.4583, 3.3194),
        "Alimosho": (6.6506, 3.2689),
        "Amuwo-Odofin": (6.4444, 3.2825),
        "Apapa": (6.4474, 3.3592),
        "Badagry": (6.4161, 2.8869),
        "Epe": (6.5833, 3.9833),
        "Eti-Osa": (6.4667, 3.6000),
        "Ibeju-Lekki": (6.4500, 3.8667),
        "Ifako-Ijaiye": (6.6667, 3.2667),
        "Ikeja": (6.5964, 3.3431),
        "Ikorodu": (6.6194, 3.5115),
        "Kosofe": (6.5833, 3.4000),
        "Lagos Island": (6.4541, 3.3947),
        "Lagos Mainland": (6.5083, 3.3778),
        "Mushin": (6.5319, 3.3431),
        "Ojo": (6.4500, 3.1833),
        "Oshodi-Isolo": (6.5333, 3.3167),
        "Shomolu": (6.5333, 3.3833),
        "Surulere": (6.4969, 3.3606),
    },
    "FCT": {
        "Abaji": (8.8667, 7.0000),
        "Abuja Municipal": (9.0579, 7.4951),
        "Bwari": (9.2833, 7.3667),
        "Gwagwalada": (8.9333, 7.0833),
        "Kuje": (8.8833, 7.2333),
        "Kwali": (8.8833, 7.0167),
    },
    "Kano": {
        "Ajingi": (11.9833, 8.7667),
        "Albasu": (11.7500, 8.5500),
        "Bagwai": (12.3833, 8.2500),
        "Bebeji": (11.6500, 8.2833),
        "Bichi": (11.7667, 8.2333),
        "Bunkure": (11.7833, 8.5333),
        "Dala": (12.0000, 8.5167),
        "Dambatta": (12.4167, 8.5167),
        "Dawakin Kudu": (11.8500, 8.6333),
        "Dawakin Tofa": (12.1167, 8.3667),
        "Doguwa": (11.4667, 8.9000),
        "Fagge": (12.0167, 8.5333),
        "Gabasawa": (12.0833, 8.2167),
        "Garko": (11.6333, 8.6500),
        "Garun Mallam": (11.4833, 8.6000),
        "Gaya": (11.8667, 9.0000),
        "Gezawa": (12.1333, 8.7000),
        "Gwale": (12.0333, 8.5000),
        "Gwarzo": (11.9167, 8.0667),
        "Kabo": (11.8333, 8.2167),
        "Kano Municipal": (12.0022, 8.5919),
        "Karaye": (11.7833, 7.8333),
        "Kibiya": (11.5167, 8.3667),
        "Kiru": (11.7667, 8.1167),
        "Kumbotso": (11.9167, 8.5333),
        "Kunchi": (12.4667, 8.9333),
        "Kura": (11.7833, 8.4333),
        "Madobi": (11.7500, 8.4833),
        "Makoda": (12.3167, 8.4000),
        "Minjibir": (12.1833, 8.6500),
        "Nasarawa": (12.0500, 8.5333),
        "Rano": (11.5500, 8.5667),
        "Rimin Gado": (12.0500, 8.3667),
        "Rogo": (11.5333, 8.7833),
        "Shanono": (12.0667, 8.1333),
        "Sumaila": (11.5167, 8.8667),
        "Takai": (12.2833, 8.5667),
        "Tarauni": (12.0333, 8.5500),
        "Tofa": (12.2167, 8.0333),
        "Tsanyawa": (12.2000, 8.8333),
        "Tudun Wada": (11.9833, 8.5500),
        "Ungogo": (12.0667, 8.4833),
        "Warawa": (11.6333, 8.9500),
        "Wudil": (11.8167, 8.8333),
    },
}


def get_states() -> List[str]:
    """Get list of all Nigerian states and FCT."""
    return sorted(list(NIGERIA_STATES.keys()))


def get_state_location(state: str) -> Tuple[float, float]:
    """Get the centroid location (lat, lon) for a state."""
    return NIGERIA_STATES.get(state)


def get_lgas_for_state(state: str) -> List[str]:
    """Get list of LGAs for a given state."""
    if state in NIGERIA_LGAS:
        return sorted(list(NIGERIA_LGAS[state].keys()))
    return []


def get_lga_location(state: str, lga: str) -> Tuple[float, float]:
    """Get the location (lat, lon) for an LGA."""
    if state in NIGERIA_LGAS and lga in NIGERIA_LGAS[state]:
        return NIGERIA_LGAS[state][lga]
    return None


def get_selected_locations(
    selected_states: List[str] = None,
    selected_lgas: Dict[str, List[str]] = None,
) -> List[Dict]:
    """
    Get locations based on selected states and LGAs.
    
    Args:
        selected_states: List of state names (if no LGAs specified, returns state centroids)
        selected_lgas: Dict mapping state to list of LGA names
    
    Returns:
        List of dicts with 'name', 'lat', 'lon', 'type', 'state'
    """
    locations = []
    
    if selected_lgas:
        # Get LGA locations
        for state, lgas in selected_lgas.items():
            for lga in lgas:
                loc = get_lga_location(state, lga)
                if loc:
                    locations.append({
                        "name": lga,
                        "lat": loc[0],
                        "lon": loc[1],
                        "type": "LGA",
                        "state": state,
                    })
    elif selected_states:
        # Get state centroids
        for state in selected_states:
            loc = get_state_location(state)
            if loc:
                locations.append({
                    "name": state,
                    "lat": loc[0],
                    "lon": loc[1],
                    "type": "State",
                    "state": state,
                })
    
    return locations
