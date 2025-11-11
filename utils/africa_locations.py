"""
Africa Locations Database
Comprehensive list of African countries with their administrative divisions
Respects each country's unique administrative structure (States, Regions, Provinces, etc.)
"""
from typing import Dict, List, Tuple

# Define administrative division types for each country
ADMIN_DIVISION_TYPES = {
    # West Africa
    "Nigeria": "State",
    "Ghana": "Region",
    "Senegal": "Region",
    "Mali": "Region",
    "Burkina Faso": "Region",
    "Niger": "Region",
    "Guinea": "Region",
    "Côte d'Ivoire": "Region",
    "Benin": "Department",
    "Togo": "Region",
    "Sierra Leone": "Province",
    "Liberia": "County",
    "Mauritania": "Region",
    "Gambia": "Division",
    "Guinea-Bissau": "Region",
    "Cape Verde": "Municipality",
    
    # East Africa
    "Kenya": "County",
    "Tanzania": "Region",
    "Uganda": "District",
    "Ethiopia": "Region",
    "Rwanda": "Province",
    "Burundi": "Province",
    "Somalia": "Region",
    "Eritrea": "Region",
    "Djibouti": "Region",
    "South Sudan": "State",
    
    # Southern Africa
    "South Africa": "Province",
    "Zimbabwe": "Province",
    "Zambia": "Province",
    "Mozambique": "Province",
    "Botswana": "District",
    "Namibia": "Region",
    "Malawi": "Region",
    "Lesotho": "District",
    "Eswatini": "Region",
    "Angola": "Province",
    
    # North Africa
    "Egypt": "Governorate",
    "Morocco": "Region",
    "Algeria": "Province",
    "Tunisia": "Governorate",
    "Libya": "District",
    "Sudan": "State",
    
    # Central Africa
    "Democratic Republic of Congo": "Province",
    "Cameroon": "Region",
    "Chad": "Region",
    "Central African Republic": "Prefecture",
    "Republic of Congo": "Department",
    "Gabon": "Province",
    "Equatorial Guinea": "Province",
    "São Tomé and Príncipe": "District",
}

# African countries with their capital cities (as default location)
AFRICA_COUNTRIES = {
    # West Africa
    "Nigeria": (9.0820, 8.6753),  # Abuja
    "Ghana": (5.6037, -0.1870),  # Accra
    "Senegal": (14.6928, -17.4467),  # Dakar
    "Mali": (12.6392, -8.0029),  # Bamako
    "Burkina Faso": (12.3714, -1.5197),  # Ouagadougou
    "Niger": (13.5127, 2.1128),  # Niamey
    "Guinea": (9.6412, -13.5784),  # Conakry
    "Côte d'Ivoire": (6.8270, -5.2893),  # Yamoussoukro
    "Benin": (6.4969, 2.6289),  # Porto-Novo
    "Togo": (6.1256, 1.2318),  # Lomé
    "Sierra Leone": (8.4657, -13.2317),  # Freetown
    "Liberia": (6.3156, -10.8074),  # Monrovia
    "Mauritania": (18.0735, -15.9582),  # Nouakchott
    "Gambia": (13.4549, -16.5790),  # Banjul
    "Guinea-Bissau": (11.8636, -15.5982),  # Bissau
    "Cape Verde": (14.9330, -23.5133),  # Praia
    
    # East Africa
    "Kenya": (-1.2864, 36.8172),  # Nairobi
    "Tanzania": (-6.7924, 39.2083),  # Dodoma
    "Uganda": (0.3476, 32.5825),  # Kampala
    "Ethiopia": (9.0320, 38.7469),  # Addis Ababa
    "Rwanda": (-1.9403, 29.8739),  # Kigali
    "Burundi": (-3.3731, 29.9189),  # Gitega
    "Somalia": (2.0469, 45.3182),  # Mogadishu
    "Eritrea": (15.3229, 38.9251),  # Asmara
    "Djibouti": (11.8251, 42.5903),  # Djibouti City
    "South Sudan": (4.8517, 31.5825),  # Juba
    
    # Southern Africa
    "South Africa": (-25.7479, 28.2293),  # Pretoria
    "Zimbabwe": (-17.8216, 31.0492),  # Harare
    "Zambia": (-15.4167, 28.2833),  # Lusaka
    "Mozambique": (-25.9655, 32.5832),  # Maputo
    "Botswana": (-24.6282, 25.9231),  # Gaborone
    "Namibia": (-22.5597, 17.0832),  # Windhoek
    "Malawi": (-13.9626, 33.7741),  # Lilongwe
    "Lesotho": (-29.3167, 27.4833),  # Maseru
    "Eswatini": (-26.3054, 31.1367),  # Mbabane
    "Angola": (-8.8390, 13.2894),  # Luanda
    
    # North Africa
    "Egypt": (30.0444, 31.2357),  # Cairo
    "Morocco": (34.0209, -6.8416),  # Rabat
    "Algeria": (36.7538, 3.0588),  # Algiers
    "Tunisia": (36.8065, 10.1815),  # Tunis
    "Libya": (32.8872, 13.1913),  # Tripoli
    "Sudan": (15.5007, 32.5599),  # Khartoum
    
    # Central Africa
    "Democratic Republic of Congo": (-4.3217, 15.3125),  # Kinshasa
    "Cameroon": (3.8480, 11.5021),  # Yaoundé
    "Chad": (12.1348, 15.0557),  # N'Djamena
    "Central African Republic": (4.3947, 18.5582),  # Bangui
    "Republic of Congo": (-4.2634, 15.2429),  # Brazzaville
    "Gabon": (0.4162, 9.4673),  # Libreville
    "Equatorial Guinea": (3.7504, 8.7371),  # Malabo
    "São Tomé and Príncipe": (0.3302, 6.7333),  # São Tomé
}

# Major administrative divisions for each country
# Format: {"Country": {"Division Name": (lat, lon)}}
AFRICA_DIVISIONS = {
    # Nigeria - States
    "Nigeria": {
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
        "FCT": (9.0765, 7.3986),
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
    },
    
    # Kenya - Counties (47 total)
    "Kenya": {
        "Nairobi": (-1.2921, 36.8219),
        "Mombasa": (-4.0435, 39.6682),
        "Kisumu": (-0.0917, 34.7680),
        "Nakuru": (-0.3031, 36.0800),
        "Uasin Gishu": (0.5143, 35.2698),
        "Kiambu": (-1.0332, 37.0693),
        "Kilifi": (-3.2167, 40.1167),
        "Kakamega": (0.2827, 34.7519),
        "Nyeri": (-0.4208, 36.9475),
        "Meru": (0.0467, 37.6500),
        "Machakos": (-1.5167, 37.2636),
        "Kitui": (-1.3667, 38.0106),
        "Garissa": (-0.4569, 39.6461),
        "Mandera": (3.9366, 41.8550),
        "Wajir": (1.7500, 40.0667),
        "Marsabit": (2.3333, 37.9833),
        "Isiolo": (0.3556, 37.5833),
        "Laikipia": (0.3667, 36.7833),
        "Nyandarua": (-0.1833, 36.4333),
        "Murang'a": (-0.7167, 37.1500),
        "Kirinyaga": (-0.4833, 37.3167),
        "Embu": (-0.5333, 37.4500),
        "Tharaka-Nithi": (-0.3167, 37.7667),
        "Kwale": (-4.1833, 39.4500),
        "Taita-Taveta": (-3.3167, 38.3500),
        "Lamu": (-2.2667, 40.9000),
        "Tana River": (-1.5167, 39.9833),
        "Bungoma": (0.5667, 34.5667),
        "Busia": (0.4333, 34.1167),
        "Siaya": (0.0667, 34.2833),
        "Migori": (-0.9333, 34.4667),
        "Homa Bay": (-0.5167, 34.4500),
        "Kisii": (-0.6833, 34.7833),
        "Nyamira": (-0.5667, 34.9333),
        "Trans Nzoia": (1.0500, 34.9500),
        "West Pokot": (1.6167, 35.1167),
        "Turkana": (3.1167, 35.6000),
        "Samburu": (1.2167, 36.8000),
        "Baringo": (0.4667, 36.0833),
        "Elgeyo-Marakwet": (0.8167, 35.4500),
        "Nandi": (0.1833, 35.1167),
        "Kericho": (-0.3667, 35.2833),
        "Bomet": (-0.7833, 35.3167),
        "Narok": (-1.0833, 35.8667),
        "Kajiado": (-2.1000, 36.7833),
        "Makueni": (-2.1667, 37.8000),
        "Vihiga": (0.0667, 34.7167),
    },
    
    # South Africa - Provinces
    "South Africa": {
        "Gauteng": (-26.2708, 28.1123),
        "Western Cape": (-33.9249, 18.4241),
        "KwaZulu-Natal": (-29.8587, 31.0218),
        "Eastern Cape": (-32.2968, 26.4194),
        "Limpopo": (-23.4013, 29.4179),
        "Mpumalanga": (-25.5653, 30.5279),
        "North West": (-26.6709, 25.4280),
        "Free State": (-28.4541, 26.8118),
        "Northern Cape": (-29.0467, 21.8569),
    },
    
    # Ghana - Regions (16 total)
    "Ghana": {
        "Greater Accra": (5.6037, -0.1870),
        "Ashanti": (6.7460, -1.5230),
        "Western": (5.2784, -2.0761),
        "Western North": (6.2833, -2.5000),
        "Eastern": (6.0891, -0.8656),
        "Central": (5.5600, -0.7520),
        "Northern": (9.4007, -0.8400),
        "Savannah": (9.0833, -1.8167),
        "North East": (10.5167, -0.3667),
        "Upper East": (10.7085, -0.9821),
        "Upper West": (10.2962, -2.1595),
        "Volta": (6.6667, 0.5000),
        "Oti": (7.6167, 0.2000),
        "Bono": (7.6667, -2.5000),
        "Bono East": (7.7500, -1.0500),
        "Ahafo": (7.5833, -2.3167),
    },
    
    # Egypt - Governorates (27 total)
    "Egypt": {
        "Cairo": (30.0444, 31.2357),
        "Alexandria": (31.2001, 29.9187),
        "Giza": (30.0131, 31.2089),
        "Port Said": (31.2653, 32.3019),
        "Suez": (29.9668, 32.5498),
        "Luxor": (25.6872, 32.6396),
        "Aswan": (24.0889, 32.8998),
        "Ismailia": (30.5965, 32.2715),
        "Dakahlia": (31.0364, 31.3812),
        "Beheira": (30.8481, 30.3436),
        "Faiyum": (29.3084, 30.8405),
        "Gharbia": (30.8754, 31.0335),
        "Kafr El Sheikh": (31.1107, 30.9388),
        "Minya": (28.0871, 30.7618),
        "Monufia": (30.5972, 30.9876),
        "Qalyubia": (30.3262, 31.2157),
        "Sharqia": (30.5965, 31.5040),
        "Sohag": (26.5569, 31.6948),
        "Asyut": (27.1809, 31.1837),
        "Beni Suef": (29.0661, 31.0994),
        "Damietta": (31.4175, 31.8144),
        "Qena": (26.1551, 32.7160),
        "Matrouh": (31.3543, 27.2373),
        "Red Sea": (27.2579, 33.8116),
        "North Sinai": (30.2801, 33.6176),
        "South Sinai": (28.6667, 33.8000),
        "New Valley": (25.4500, 30.5500),
    },
    
    # Ethiopia - Regions (12 total)
    "Ethiopia": {
        "Addis Ababa": (9.0320, 38.7469),
        "Oromia": (8.5400, 39.2700),
        "Amhara": (11.5000, 38.5000),
        "Tigray": (14.0000, 39.0000),
        "Somali": (6.5000, 43.5000),
        "Afar": (11.7500, 41.0000),
        "Southern Nations": (6.5000, 37.0000),
        "Sidama": (6.4900, 38.4900),
        "Dire Dawa": (9.6011, 41.8500),
        "Harari": (9.3133, 42.1331),
        "Gambela": (8.2500, 34.5833),
        "Benishangul-Gumuz": (10.7833, 35.5667),
    },
    
    # Morocco - Regions (12 total)
    "Morocco": {
        "Casablanca-Settat": (33.5731, -7.5898),
        "Rabat-Salé-Kénitra": (34.0209, -6.8416),
        "Marrakesh-Safi": (31.6295, -7.9811),
        "Fès-Meknès": (34.0181, -5.0078),
        "Tangier-Tétouan-Al Hoceïma": (35.5889, -5.3626),
        "Oriental": (34.6814, -2.9336),
        "Béni Mellal-Khénifra": (32.3372, -6.3498),
        "Souss-Massa": (30.4278, -9.5981),
        "Drâa-Tafilalet": (31.9314, -4.4333),
        "Guelmim-Oued Noun": (28.9870, -10.0574),
        "Laâyoune-Sakia El Hamra": (27.1536, -13.2033),
        "Dakhla-Oued Ed-Dahab": (23.7146, -15.9582),
    },
    
    # Tanzania - Regions (31 total)
    "Tanzania": {
        "Dar es Salaam": (-6.7924, 39.2083),
        "Dodoma": (-6.1630, 35.7516),
        "Arusha": (-3.3869, 36.6830),
        "Mwanza": (-2.5164, 32.9175),
        "Mbeya": (-8.9000, 33.4500),
        "Morogoro": (-6.8211, 37.6636),
        "Tanga": (-5.0689, 39.0986),
        "Mara": (-1.7750, 34.8667),
        "Kilimanjaro": (-3.3587, 37.3484),
        "Tabora": (-5.0167, 32.8000),
        "Kigoma": (-4.8769, 29.6267),
        "Ruvuma": (-10.7000, 35.7500),
        "Iringa": (-7.7700, 35.6900),
        "Kagera": (-1.3000, 31.8000),
        "Mtwara": (-10.2692, 40.1836),
        "Pwani (Coast)": (-7.1333, 39.0833),
        "Shinyanga": (-3.6636, 33.4217),
        "Rukwa": (-7.9833, 31.3333),
        "Singida": (-4.8167, 34.7333),
        "Lindi": (-10.0000, 39.7167),
        "Geita": (-2.8711, 32.2294),
        "Katavi": (-6.3667, 31.2500),
        "Njombe": (-9.3333, 34.7667),
        "Simiyu": (-2.8417, 34.1536),
        "Songwe": (-9.2167, 33.4667),
    },
    
    # Uganda - Districts (Major regions, 20 selected)
    "Uganda": {
        "Kampala": (0.3476, 32.5825),
        "Wakiso": (0.4044, 32.4594),
        "Mukono": (0.3536, 32.7553),
        "Jinja": (0.4244, 33.2042),
        "Mbale": (1.0644, 34.1750),
        "Gulu": (2.7742, 32.2992),
        "Lira": (2.2497, 32.8994),
        "Mbarara": (-0.6103, 30.6580),
        "Kasese": (0.1833, 30.0833),
        "Masaka": (-0.3336, 31.7344),
        "Hoima": (1.4331, 31.3522),
        "Fort Portal": (0.6719, 30.2750),
        "Soroti": (1.7150, 33.6114),
        "Arua": (3.0200, 30.9108),
        "Kabale": (-1.2486, 29.9894),
        "Kitgum": (3.2817, 32.8867),
        "Moroto": (2.5347, 34.6664),
        "Tororo": (0.6928, 34.1808),
        "Rukungiri": (-0.7883, 29.9397),
        "Bushenyi": (-0.5417, 30.1917),
    },
    
    # Zimbabwe - Provinces (10 total)
    "Zimbabwe": {
        "Harare": (-17.8216, 31.0492),
        "Bulawayo": (-20.1500, 28.5833),
        "Manicaland": (-18.9667, 32.6500),
        "Mashonaland Central": (-16.7667, 31.1167),
        "Mashonaland East": (-18.2667, 31.5167),
        "Mashonaland West": (-17.8500, 29.8167),
        "Masvingo": (-20.0639, 30.8311),
        "Matabeleland North": (-18.5000, 27.5000),
        "Matabeleland South": (-21.0500, 29.0167),
        "Midlands": (-19.4500, 29.8167),
    },
    
    # Zambia - Provinces (10 total)
    "Zambia": {
        "Lusaka": (-15.4167, 28.2833),
        "Copperbelt": (-12.8389, 28.2136),
        "Central": (-13.8333, 28.2833),
        "Eastern": (-13.5333, 32.6500),
        "Luapula": (-11.1667, 29.3333),
        "Northern": (-10.2000, 31.1833),
        "North-Western": (-12.1833, 25.8500),
        "Southern": (-16.7500, 27.3333),
        "Western": (-15.3167, 23.1167),
        "Muchinga": (-11.0500, 31.7500),
    },
    
    # Algeria - Provinces (Wilayas, 20 major)
    "Algeria": {
        "Algiers": (36.7538, 3.0588),
        "Oran": (35.6969, -0.6331),
        "Constantine": (36.3650, 6.6147),
        "Annaba": (36.9000, 7.7667),
        "Blida": (36.4800, 2.8278),
        "Batna": (35.5558, 6.1742),
        "Sétif": (36.1905, 5.4103),
        "Tlemcen": (34.8781, -1.3153),
        "Béjaïa": (36.7525, 5.0556),
        "Biskra": (34.8503, 5.7242),
        "Tébessa": (35.4036, 8.1206),
        "Tiaret": (35.3708, 1.3228),
        "Ouargla": (31.9492, 5.3347),
        "Ghardaïa": (32.4839, 3.6736),
        "Adrar": (27.8742, 0.2036),
        "Tindouf": (27.6764, -8.1475),
        "Béchar": (31.6178, -2.2158),
        "Tamanrasset": (22.7853, 5.5228),
        "Illizi": (26.5089, 8.4831),
        "Djelfa": (34.6703, 3.2631),
    },
    
    # Tunisia - Governorates (24 total)
    "Tunisia": {
        "Tunis": (36.8065, 10.1815),
        "Sfax": (34.7406, 10.7603),
        "Sousse": (35.8256, 10.6369),
        "Kairouan": (35.6781, 10.0963),
        "Bizerte": (37.2744, 9.8739),
        "Gabès": (33.8815, 10.0982),
        "Ariana": (36.8625, 10.1956),
        "Gafsa": (34.4250, 8.7842),
        "Monastir": (35.7778, 10.8264),
        "Ben Arous": (36.7542, 10.2189),
        "Kasserine": (35.1675, 8.8364),
        "Médenine": (33.3547, 10.5053),
        "Nabeul": (36.4561, 10.7339),
        "Tataouine": (32.9297, 10.4517),
        "Béja": (36.7256, 9.1817),
        "Jendouba": (36.5011, 8.7806),
        "Mahdia": (35.5047, 11.0622),
        "Manouba": (36.8081, 10.0969),
        "Sidi Bouzid": (35.0381, 9.4839),
        "Siliana": (36.0850, 9.3708),
        "Tozeur": (33.9197, 8.1339),
        "Zaghouan": (36.4028, 10.1428),
        "Kef": (36.1742, 8.7050),
        "Kebili": (33.7047, 8.9692),
    },
    
    # Cameroon - Regions (10 total)
    "Cameroon": {
        "Centre": (3.8480, 11.5021),
        "Littoral": (4.0511, 9.7679),
        "West": (5.4769, 10.4178),
        "Northwest": (6.2072, 10.1547),
        "Southwest": (4.1561, 9.2325),
        "Adamawa": (7.3697, 13.5844),
        "East": (4.5567, 14.5164),
        "Far North": (10.5917, 14.2123),
        "North": (8.9806, 13.3869),
        "South": (2.9261, 11.5214),
    },
    
    # Senegal - Regions (14 total)
    "Senegal": {
        "Dakar": (14.6928, -17.4467),
        "Thiès": (14.7886, -16.9261),
        "Diourbel": (14.6500, -16.2333),
        "Fatick": (14.3406, -16.4108),
        "Kaolack": (14.1500, -16.0667),
        "Kolda": (12.9094, -14.9500),
        "Louga": (15.6139, -16.2306),
        "Matam": (15.6558, -13.2553),
        "Saint-Louis": (16.0175, -16.4889),
        "Sédhiou": (12.7083, -15.5567),
        "Tambacounda": (13.7708, -13.6681),
        "Kédougou": (12.5600, -12.1747),
        "Kaffrine": (14.1061, -15.5478),
        "Ziguinchor": (12.5833, -16.2731),
    },
    
    # Mali - Regions (8 regions + 1 district)
    "Mali": {
        "Bamako": (12.6392, -8.0029),  # Capital District
        "Kayes": (14.4464, -11.4333),
        "Koulikoro": (12.8625, -7.5594),
        "Sikasso": (11.3175, -5.6667),
        "Ségou": (13.4317, -6.2633),
        "Mopti": (14.4948, -4.1939),
        "Tombouctou": (16.7666, -3.0026),
        "Gao": (16.2710, -0.0418),
        "Kidal": (18.4411, 1.4078),
    },
    
    # Mozambique - Provinces (11 total)
    "Mozambique": {
        "Maputo City": (-25.9655, 32.5832),
        "Maputo": (-25.0653, 32.4033),
        "Gaza": (-23.5733, 33.2267),
        "Inhambane": (-23.8650, 35.3833),
        "Sofala": (-19.8436, 34.8389),
        "Manica": (-18.9422, 32.8722),
        "Tete": (-16.1564, 33.5867),
        "Zambézia": (-17.1167, 37.1167),
        "Nampula": (-15.1194, 39.2667),
        "Cabo Delgado": (-12.3400, 40.3569),
        "Niassa": (-13.2678, 36.5636),
    },
    
    # Togo - Regions (5 total)
    "Togo": {
        "Maritime": (6.2167, 1.2500),  # Lomé region
        "Plateaux": (7.0000, 1.1667),
        "Centrale": (8.5167, 1.0000),
        "Kara": (9.5500, 1.1833),
        "Savanes": (10.8667, 0.5000),
    },
    
    # Benin - Departments (12 total) 
    "Benin": {
        "Littoral": (6.4969, 2.6289),  # Cotonou/Porto-Novo
        "Atlantique": (6.4500, 2.2500),
        "Ouémé": (6.7500, 2.6167),
        "Plateau": (7.2500, 2.4167),
        "Mono": (6.5000, 1.7500),
        "Couffo": (7.0000, 2.0000),
        "Zou": (7.2500, 2.2500),
        "Collines": (7.8833, 2.3333),
        "Donga": (9.0000, 1.5500),
        "Borgou": (9.7500, 2.7500),
        "Alibori": (11.1167, 2.8833),
        "Atacora": (10.5000, 1.5000),
    },
}



def get_countries() -> List[str]:
    """Get list of all African countries"""
    return sorted(AFRICA_COUNTRIES.keys())


def get_admin_division_type(country: str) -> str:
    """Get the administrative division type for a country (State, Region, Province, etc.)"""
    return ADMIN_DIVISION_TYPES.get(country, "Region")


def get_divisions_for_country(country: str) -> List[str]:
    """Get list of administrative divisions for a specific country"""
    if country in AFRICA_DIVISIONS:
        return sorted(AFRICA_DIVISIONS[country].keys())
    return []


def get_country_location(country: str) -> Tuple[float, float]:
    """Get the capital city coordinates for a country"""
    return AFRICA_COUNTRIES.get(country, (0.0, 0.0))


def get_division_location(country: str, division: str) -> Tuple[float, float]:
    """Get coordinates for a specific division within a country"""
    if country in AFRICA_DIVISIONS and division in AFRICA_DIVISIONS[country]:
        return AFRICA_DIVISIONS[country][division]
    return (0.0, 0.0)


# Sub-divisions (LGAs for Nigeria, Sub-counties for Kenya, Districts for others, etc.)
# Format: {Country: {Division: {Sub-division: (lat, lon)}}}
AFRICA_SUB_DIVISIONS = {
    # Nigeria - LGAs (Local Government Areas)
    "Nigeria": {
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
            "Dala": (12.0000, 8.5167),
            "Fagge": (12.0167, 8.5333),
            "Gwale": (12.0333, 8.5000),
            "Kano Municipal": (12.0022, 8.5919),
            "Kumbotso": (11.9167, 8.5333),
            "Nasarawa": (12.0500, 8.5333),
            "Tarauni": (12.0333, 8.5500),
            "Ungogo": (12.0667, 8.4833),
        },
        "Adamawa": {
            "Yola North": (9.2080, 12.4533),
            "Yola South": (9.1827, 12.4380),
            "Fufore": (9.2667, 12.6500),
            "Girei": (9.3333, 12.5500),
            "Mubi North": (10.2667, 13.2667),
            "Mubi South": (10.1667, 13.2000),
            "Ganye": (8.4333, 12.0667),
            "Song": (9.7667, 12.5667),
            "Demsa": (9.4500, 12.1667),
            "Numan": (9.4667, 12.0333),
            "Mayo-Belwa": (9.0000, 12.0667),
        },
        "Rivers": {
            "Port Harcourt": (4.8156, 7.0498),
            "Obio-Akpor": (5.0021, 6.8815),
            "Eleme": (4.7667, 7.1167),
            "Ikwerre": (5.0333, 6.9500),
            "Emohua": (5.0000, 6.7667),
            "Okrika": (4.7333, 7.0833),
            "Ogu-Bolo": (4.6667, 7.1667),
            "Oyigbo": (4.8833, 7.1333),
            "Degema": (4.7500, 6.7667),
        },
        "Kaduna": {
            "Kaduna North": (10.5667, 7.4333),
            "Kaduna South": (10.4667, 7.4167),
            "Chikun": (10.5833, 7.2833),
            "Igabi": (10.8333, 7.5833),
            "Zaria": (11.0667, 7.7000),
            "Sabon Gari": (11.1500, 7.7000),
            "Giwa": (11.5333, 7.7000),
            "Kajuru": (10.3333, 7.6833),
            "Kachia": (9.8667, 7.9167),
        },
        "Oyo": {
            "Ibadan North": (7.4000, 3.9000),
            "Ibadan South-West": (7.3667, 3.9000),
            "Ibadan North-East": (7.4333, 3.9333),
            "Ibadan South-East": (7.3500, 3.9167),
            "Ibadan North-West": (7.4167, 3.8833),
            "Egbeda": (7.3833, 3.9667),
            "Akinyele": (7.5333, 3.9667),
            "Lagelu": (7.4500, 3.8833),
            "Ido": (7.4833, 3.7500),
            "Oluyole": (7.2833, 3.8500),
        },
        "Enugu": {
            "Enugu East": (6.4500, 7.5167),
            "Enugu North": (6.4833, 7.5000),
            "Enugu South": (6.4167, 7.4833),
            "Nkanu East": (6.3667, 7.6167),
            "Nkanu West": (6.3167, 7.5333),
            "Udi": (6.3167, 7.4000),
            "Nsukka": (6.8500, 7.3833),
            "Igbo-Etiti": (6.6833, 7.5333),
            "Oji River": (6.3167, 7.3833),
        },
        "Ogun": {
            "Abeokuta South": (7.1500, 3.3500),
            "Abeokuta North": (7.1833, 3.3500),
            "Ado-Odo/Ota": (6.6833, 3.1667),
            "Ifo": (6.8167, 3.1833),
            "Sagamu": (6.8333, 3.6500),
            "Ijebu Ode": (6.8167, 3.9167),
            "Ijebu North": (6.9000, 3.9333),
            "Remo North": (6.9167, 3.6000),
            "Obafemi Owode": (6.9500, 3.5000),
        },
        "Anambra": {
            "Awka North": (6.2333, 7.0833),
            "Awka South": (6.2000, 7.0833),
            "Onitsha North": (6.1500, 6.7833),
            "Onitsha South": (6.1333, 6.7667),
            "Nnewi North": (6.0167, 6.9167),
            "Nnewi South": (5.9667, 6.9333),
            "Aguata": (6.0333, 7.0833),
            "Anaocha": (6.1500, 7.0333),
            "Dunukofia": (6.1333, 6.9000),
        },
        "Plateau": {
            "Jos North": (9.9167, 8.9000),
            "Jos South": (9.8500, 8.8667),
            "Jos East": (9.8833, 9.0000),
            "Barikin Ladi": (9.5333, 8.9000),
            "Riyom": (9.6333, 8.7667),
            "Bokkos": (9.3000, 9.0000),
            "Mangu": (9.5333, 9.1000),
            "Pankshin": (9.3167, 9.4333),
        },
        "Abia": {
            "Aba North": (5.1333, 7.3667),
            "Aba South": (5.1000, 7.3500),
            "Umuahia North": (5.5333, 7.4833),
            "Umuahia South": (5.5000, 7.4833),
            "Arochukwu": (5.3833, 7.9167),
            "Bende": (5.5667, 7.6333),
            "Ikwuano": (5.4333, 7.6000),
            "Isiala Ngwa North": (5.4167, 7.3500),
            "Isiala Ngwa South": (5.3667, 7.3333),
            "Ohafia": (5.6167, 7.8000),
            "Osisioma": (5.1500, 7.4000),
            "Ugwunagbo": (5.0833, 7.4333),
            "Ukwa East": (4.9667, 7.4833),
            "Ukwa West": (4.9333, 7.4167),
        },
        "Akwa Ibom": {
            "Uyo": (5.0500, 7.9333),
            "Eket": (4.6500, 7.9333),
            "Ikot Ekpene": (5.1833, 7.7167),
            "Abak": (4.9833, 7.7833),
            "Oron": (4.8167, 8.2333),
            "Etinan": (4.8333, 7.8500),
            "Ikot Abasi": (4.5667, 7.5333),
            "Essien Udim": (5.0667, 7.6833),
            "Itu": (5.2000, 8.0000),
        },
        "Delta": {
            "Warri South": (5.5167, 5.7500),
            "Warri North": (5.5667, 5.7333),
            "Uvwie": (5.5833, 5.8167),
            "Ughelli North": (5.5000, 6.0000),
            "Ughelli South": (5.4333, 5.9833),
            "Sapele": (5.8833, 5.6833),
            "Ethiope East": (5.9167, 6.0833),
            "Okpe": (5.6167, 5.8833),
            "Udu": (5.4833, 5.8000),
        },
        "Edo": {
            "Oredo": (6.3333, 5.6167),
            "Egor": (6.3667, 5.6500),
            "Ikpoba-Okha": (6.3500, 5.6833),
            "Ovia North-East": (6.4500, 5.7667),
            "Ovia South-West": (6.3167, 5.5167),
            "Uhunmwonde": (6.4167, 5.7333),
            "Owan East": (6.9667, 6.2333),
            "Owan West": (7.0500, 5.9833),
            "Akoko-Edo": (7.3667, 6.1000),
        },
        "Bayelsa": {
            "Yenagoa": (4.9167, 6.2667),
            "Sagbama": (5.1667, 6.2000),
            "Ekeremor": (5.0500, 5.6000),
            "Kolokuma/Opokuma": (5.0833, 6.1333),
            "Brass": (4.3167, 6.2500),
            "Ogbia": (4.7000, 6.3000),
            "Nembe": (4.5333, 6.4000),
            "Southern Ijaw": (4.7500, 6.0000),
        },
        "Benue": {
            "Makurdi": (7.7333, 8.5333),
            "Gboko": (7.3167, 9.0000),
            "Otukpo": (7.1833, 8.1333),
            "Oju": (6.8500, 8.3833),
            "Katsina-Ala": (7.1667, 9.2667),
            "Gwer West": (7.5667, 8.3167),
            "Gwer East": (7.6167, 8.6667),
            "Buruku": (7.6833, 9.0167),
        },
        "Borno": {
            "Maiduguri": (11.8333, 13.1500),
            "Biu": (10.6167, 12.1833),
            "Damboa": (11.1500, 12.7500),
            "Dikwa": (12.0333, 13.9167),
            "Gwoza": (11.0833, 13.7000),
            "Jere": (11.8667, 13.2500),
            "Kaga": (12.1000, 13.6833),
            "Konduga": (11.6833, 13.4333),
            "Mafa": (11.9833, 13.6833),
        },
        "Cross River": {
            "Calabar Municipal": (4.9500, 8.3333),
            "Calabar South": (4.9167, 8.3167),
            "Akamkpa": (5.0167, 8.1333),
            "Odukpani": (5.1333, 8.2500),
            "Ikom": (5.9667, 8.7167),
            "Ogoja": (6.6500, 8.8000),
            "Obudu": (6.6667, 9.1667),
            "Obubra": (5.9833, 8.3333),
        },
        "Ebonyi": {
            "Abakaliki": (6.3167, 8.1167),
            "Afikpo North": (5.8833, 7.9333),
            "Afikpo South": (5.8333, 7.9500),
            "Ebonyi": (6.0667, 8.0500),
            "Ezza North": (6.3667, 8.0167),
            "Ezza South": (6.2667, 8.0333),
            "Ikwo": (6.2333, 8.0833),
            "Ishielu": (6.4167, 8.1833),
            "Ivo": (5.8167, 7.8667),
        },
        "Ekiti": {
            "Ado-Ekiti": (7.6167, 5.2167),
            "Ikere": (7.4833, 5.2333),
            "Ikole": (7.8000, 5.5167),
            "Ise/Orun": (7.4667, 5.4333),
            "Ijero": (7.8167, 5.0667),
            "Efon": (7.6833, 4.9167),
            "Emure": (7.4333, 5.4667),
            "Gbonyin": (7.6500, 5.3167),
        },
        "Gombe": {
            "Gombe": (10.2833, 11.1667),
            "Akko": (10.3500, 11.0333),
            "Balanga": (9.8333, 11.4167),
            "Billiri": (9.8667, 11.2167),
            "Dukku": (10.8000, 10.8167),
            "Funakaye": (10.4667, 11.4833),
            "Kaltungo": (9.8167, 11.3000),
            "Kwami": (10.1500, 11.2667),
        },
        "Imo": {
            "Owerri Municipal": (5.4833, 7.0333),
            "Owerri North": (5.5333, 7.0500),
            "Owerri West": (5.4833, 6.9667),
            "Orlu": (5.7833, 7.0333),
            "Okigwe": (5.8333, 7.3500),
            "Mbaitoli": (5.4833, 7.0000),
            "Nkwerre": (5.7500, 7.1167),
            "Ehime Mbano": (5.6833, 7.1833),
            "Oguta": (5.7167, 6.8083),
        },
        "Jigawa": {
            "Dutse": (11.7500, 9.3333),
            "Hadejia": (12.4500, 10.0333),
            "Birnin Kudu": (11.4500, 9.4833),
            "Gumel": (12.6333, 9.3833),
            "Kazaure": (12.6500, 8.4167),
            "Ringim": (12.1500, 9.1667),
            "Jahun": (12.0833, 9.6333),
            "Maigatari": (12.7833, 9.4333),
        },
        "Kebbi": {
            "Birnin Kebbi": (12.4500, 4.1833),
            "Argungu": (12.7500, 4.5167),
            "Yauri": (11.0000, 4.4833),
            "Zuru": (11.4333, 5.2333),
            "Gwandu": (12.4667, 4.6500),
            "Jega": (12.2167, 4.3833),
            "Kalgo": (12.3333, 4.1833),
            "Maiyama": (12.0833, 4.3167),
        },
        "Kogi": {
            "Lokoja": (7.8000, 6.7333),
            "Okene": (7.5500, 6.2333),
            "Kabba": (7.8167, 6.0833),
            "Idah": (7.1167, 6.7333),
            "Ankpa": (7.4000, 7.6333),
            "Ajaokuta": (7.5667, 6.6500),
            "Dekina": (7.6833, 7.0500),
            "Ofu": (7.1167, 6.9333),
            "Ogori/Magongo": (7.7667, 6.1167),
        },
        "Kwara": {
            "Ilorin South": (8.4833, 4.5500),
            "Ilorin West": (8.5000, 4.5333),
            "Ilorin East": (8.5167, 4.5667),
            "Asa": (8.5500, 4.4667),
            "Offa": (8.1500, 4.7167),
            "Pategi": (8.7167, 5.7500),
            "Edu": (9.0833, 5.0500),
            "Baruten": (9.3833, 3.7833),
        },
        "Nasarawa": {
            "Lafia": (8.4833, 8.5000),
            "Keffi": (8.8500, 7.8833),
            "Akwanga": (8.9000, 8.4167),
            "Nasarawa": (8.5333, 7.7000),
            "Karu": (9.0000, 7.6333),
            "Doma": (8.3667, 8.3833),
            "Keana": (8.1333, 8.7667),
            "Obi": (8.4333, 8.7167),
        },
        "Niger": {
            "Minna": (9.6167, 6.5500),
            "Suleja": (9.1833, 7.1833),
            "Bida": (9.0833, 6.0167),
            "Kontagora": (10.4000, 5.4667),
            "Mokwa": (9.2833, 5.0500),
            "Lapai": (9.0500, 6.5667),
            "Rijau": (10.8500, 5.2667),
            "Agwara": (10.9167, 4.2167),
        },
        "Ondo": {
            "Akure South": (7.2500, 5.2000),
            "Akure North": (7.3167, 5.2167),
            "Ondo West": (7.0833, 4.8333),
            "Ondo East": (7.1167, 4.9500),
            "Owo": (7.1967, 5.5867),
            "Idanre": (7.1167, 5.1167),
            "Ile Oluji/Okeigbo": (7.2333, 4.8167),
            "Okitipupa": (6.5000, 4.7833),
        },
        "Osun": {
            "Osogbo": (7.7667, 4.5667),
            "Ife Central": (7.4833, 4.5667),
            "Ife East": (7.5333, 4.5833),
            "Ilesa East": (7.6167, 4.7333),
            "Ilesa West": (7.6000, 4.7167),
            "Iwo": (7.6333, 4.1833),
            "Ede North": (7.7333, 4.4333),
            "Ede South": (7.7167, 4.4167),
        },
        "Sokoto": {
            "Sokoto North": (13.0833, 5.2500),
            "Sokoto South": (13.0167, 5.2167),
            "Wamako": (13.0167, 5.1333),
            "Bodinga": (12.8500, 5.1500),
            "Tambuwal": (12.4167, 4.6500),
            "Gudu": (12.6667, 4.5833),
            "Gwadabawa": (13.3500, 5.2333),
            "Illela": (13.7333, 5.2833),
        },
        "Taraba": {
            "Jalingo": (8.8833, 11.3667),
            "Wukari": (7.8667, 9.7833),
            "Ibi": (8.1833, 9.7500),
            "Takum": (7.2667, 9.9833),
            "Zing": (9.1667, 11.6167),
            "Gassol": (8.5500, 10.4500),
            "Bali": (8.0167, 11.0167),
            "Sardauna": (7.2000, 11.6833),
        },
        "Yobe": {
            "Damaturu": (11.7500, 11.9667),
            "Potiskum": (11.7167, 11.0833),
            "Gashua": (12.8667, 11.0333),
            "Nguru": (12.8667, 10.4500),
            "Geidam": (12.8833, 11.9167),
            "Fika": (11.3833, 11.4167),
            "Fune": (11.5333, 11.4833),
            "Gujba": (11.8667, 12.1667),
        },
        "Zamfara": {
            "Gusau": (12.1667, 6.6667),
            "Kaura Namoda": (12.5833, 6.5833),
            "Talata Mafara": (12.5667, 6.0667),
            "Anka": (12.1167, 5.9167),
            "Bungudu": (12.2667, 6.5667),
            "Tsafe": (11.9500, 6.9167),
            "Maru": (12.3333, 6.4000),
            "Zurmi": (12.7167, 6.7333),
        },
    },
    
    # Kenya - Sub-counties (for Nairobi County)
    "Kenya": {
        "Nairobi": {
            "Westlands": (-1.2676, 36.8059),
            "Dagoretti North": (-1.2955, 36.7418),
            "Dagoretti South": (-1.3126, 36.7271),
            "Langata": (-1.3530, 36.7441),
            "Kibra": (-1.3133, 36.7869),
            "Roysambu": (-1.2280, 36.8910),
            "Kasarani": (-1.2233, 36.8992),
            "Ruaraka": (-1.2561, 36.8814),
            "Embakasi South": (-1.3134, 36.8925),
            "Embakasi North": (-1.2641, 36.9065),
            "Embakasi Central": (-1.2974, 36.9024),
            "Embakasi East": (-1.2872, 36.9285),
            "Embakasi West": (-1.3040, 36.8696),
            "Makadara": (-1.2959, 36.8440),
            "Kamukunji": (-1.2800, 36.8360),
            "Starehe": (-1.2756, 36.8282),
            "Mathare": (-1.2606, 36.8585),
        },
    },
    
    # South Africa - Municipalities (for Gauteng Province)
    "South Africa": {
        "Gauteng": {
            "City of Johannesburg": (-26.2041, 28.0473),
            "City of Tshwane (Pretoria)": (-25.7479, 28.2293),
            "Ekurhuleni": (-26.1596, 28.2415),
            "City of Cape Town": (-33.9249, 18.4241),
            "Sedibeng": (-26.6389, 27.8581),
            "West Rand": (-26.1594, 27.8058),
        },
        "Western Cape": {
            "City of Cape Town": (-33.9249, 18.4241),
            "Cape Winelands": (-33.7292, 19.1217),
            "Overberg": (-34.4219, 19.8732),
            "West Coast": (-32.7964, 18.2786),
            "Garden Route": (-34.0366, 22.6279),
        },
    },
    
    # Ghana - Districts (for Greater Accra Region)
    "Ghana": {
        "Greater Accra": {
            "Accra Metropolitan": (5.6037, -0.1870),
            "Tema Metropolitan": (5.6698, -0.0166),
            "Ga South Municipal": (5.5800, -0.2500),
            "Ga Central Municipal": (5.6800, -0.2700),
            "Ga West Municipal": (5.7200, -0.3500),
            "Ga East Municipal": (5.7500, -0.1800),
            "Adentan Municipal": (5.7100, -0.1700),
            "Ashaiman Municipal": (5.6950, -0.0300),
            "Ledzokuku": (5.6300, -0.0800),
            "Kpone Katamanso": (5.7000, 0.0500),
        },
    },
    
    # Mali - Cercles (major communes/districts by region)
    "Mali": {
        "Bamako": {
            "Commune I": (12.6533, -8.0000),
            "Commune II": (12.6367, -7.9917),
            "Commune III": (12.6300, -7.9833),
            "Commune IV": (12.6200, -7.9750),
            "Commune V": (12.6100, -7.9667),
            "Commune VI": (12.6000, -7.9583),
        },
        "Kayes": {
            "Kayes Cercle": (14.4464, -11.4333),
            "Bafoulabé": (13.8061, -10.8317),
            "Kita": (13.0333, -9.4833),
            "Nioro du Sahel": (15.2333, -9.5833),
            "Diéma": (14.5833, -9.2167),
            "Yélimané": (15.1333, -10.5667),
            "Oussoubidiagna": (14.7167, -11.7167),
        },
        "Koulikoro": {
            "Kati": (12.7444, -8.0722),
            "Kolokani": (13.5667, -8.0333),
            "Nara": (15.1667, -7.2833),
            "Banamba": (13.5500, -7.4500),
            "Kangaba": (11.9333, -8.4167),
            "Dioïla": (12.4833, -6.8000),
            "Fana": (12.7333, -5.9000),
        },
        "Sikasso": {
            "Sikasso Cercle": (11.3175, -5.6667),
            "Bougouni": (11.4167, -7.4833),
            "Yanfolila": (11.1667, -8.2000),
            "Kolondiéba": (11.0833, -6.8833),
            "Kadiolo": (10.5500, -5.8000),
            "Koutiala": (12.3900, -5.4600),
            "Yorosso": (12.3667, -4.7833),
        },
        "Ségou": {
            "Ségou Cercle": (13.4317, -6.2633),
            "Bla": (12.2889, -5.2403),
            "Baraouéli": (12.7833, -6.5333),
            "Macina": (13.9667, -5.3667),
            "Tominian": (12.7667, -3.9333),
            "San": (13.3000, -4.9000),
            "Niono": (14.2500, -5.9833),
        },
        "Mopti": {
            "Mopti Cercle": (14.4948, -4.1939),
            "Djenné": (13.9061, -4.5533),
            "Tenenkou": (14.4500, -4.9167),
            "Youwarou": (15.9667, -2.8833),
            "Douentza": (15.0000, -2.9500),
            "Koro": (14.1500, -3.0833),
            "Bandiagara": (14.3500, -3.6167),
        },
        "Tombouctou": {
            "Tombouctou Cercle": (16.7666, -3.0026),
            "Diré": (16.3167, -3.4000),
            "Niafunké": (16.1333, -3.9833),
            "Goundam": (16.4167, -3.6667),
            "Gourma-Rharous": (16.8833, -1.9500),
        },
        "Gao": {
            "Gao Cercle": (16.2710, -0.0418),
            "Bourem": (17.0000, -0.3667),
            "Ansongo": (15.6667, 0.5000),
            "Ménaka": (15.9167, 2.4000),
        },
        "Kidal": {
            "Kidal Cercle": (18.4411, 1.4078),
            "Abeibara": (19.1667, 0.2833),
            "Tessalit": (20.2000, 1.0167),
            "Tin-Essako": (19.6667, -0.1167),
        },
    },
    
    # Egypt - Districts/Neighborhoods (for Cairo Governorate)
    "Egypt": {
        "Cairo": {
            "Nasr City": (30.0444, 31.3785),
            "Heliopolis": (30.0908, 31.3283),
            "Maadi": (29.9602, 31.2569),
            "Zamalek": (30.0618, 31.2194),
            "Downtown Cairo": (30.0444, 31.2357),
            "Giza": (30.0131, 31.2089),
            "6th of October City": (29.9537, 31.0127),
            "New Cairo": (30.0272, 31.4913),
        },
    },
    
    # Ghana - Districts (expanded to all 16 regions)
    "Ghana": {
        "Greater Accra": {
            "Accra Metropolitan": (5.6037, -0.1870),
            "Tema Metropolitan": (5.6698, -0.0166),
            "Ga South Municipal": (5.5800, -0.2500),
            "Ga Central Municipal": (5.6800, -0.2700),
            "Ga West Municipal": (5.7200, -0.3500),
            "Ga East Municipal": (5.7500, -0.1800),
            "Adentan Municipal": (5.7100, -0.1700),
            "Ashaiman Municipal": (5.6950, -0.0300),
            "Ledzokuku": (5.6300, -0.0800),
            "Kpone Katamanso": (5.7000, 0.0500),
        },
        "Ashanti": {
            "Kumasi Metropolitan": (6.7460, -1.5230),
            "Obuasi Municipal": (6.2028, -1.6703),
            "Ejisu": (6.7333, -1.3667),
            "Juaben Municipal": (6.7167, -1.3333),
            "Bosomtwe": (6.5167, -1.4333),
            "Atwima Kwanwoma": (6.8167, -1.7000),
            "Kwabre East": (6.8500, -1.4500),
            "Afigya Kwabre South": (6.7833, -1.4167),
        },
        "Western": {
            "Sekondi-Takoradi Metropolitan": (4.9344, -1.7892),
            "Shama": (5.0167, -1.6500),
            "Ahanta West": (5.2833, -2.2500),
            "Nzema East Municipal": (5.1000, -2.7500),
            "Ellembelle": (5.0500, -2.8833),
            "Wassa East": (5.7833, -1.9167),
            "Tarkwa-Nsuaem Municipal": (5.3000, -2.0000),
        },
        "Eastern": {
            "New-Juaben Municipal": (6.0891, -0.8656),
            "Akuapim North": (5.8833, -0.1167),
            "West Akim": (6.2000, -0.7333),
            "East Akim": (6.1333, -0.6333),
            "Fanteakwa South": (6.0167, -0.4833),
            "Suhum": (6.0500, -0.4500),
            "Yilo Krobo": (6.1000, -0.0833),
        },
        "Northern": {
            "Tamale Metropolitan": (9.4007, -0.8400),
            "Sagnarigu Municipal": (9.4667, -0.9333),
            "Tolon": (9.5000, -1.0167),
            "Kumbungu": (9.5667, -0.8667),
            "Savelugu Municipal": (9.6333, -0.8167),
            "Zabzugu": (9.3167, -0.3833),
        },
        "Central": {
            "Cape Coast Metropolitan": (5.1311, -1.2464),
            "Komenda-Edina-Eguafo-Abirem Municipal": (5.0833, -1.3000),
            "Abura-Asebu-Kwamankese": (5.3000, -1.1833),
            "Mfantsiman Municipal": (5.4667, -0.8333),
            "Awutu Senya East Municipal": (5.5833, -0.5167),
            "Effutu Municipal": (5.6833, -0.6167),
        },
    },
    
    # Togo - Prefectures (major districts by region)
    "Togo": {
        "Maritime": {
            "Golfe": (6.1256, 1.2318),  # Lomé
            "Lacs": (6.3333, 1.5000),
            "Vo": (6.3167, 1.4833),
            "Yoto": (6.5167, 1.3500),
            "Zio": (6.4333, 1.2167),
            "Bas-Mono": (6.2500, 1.1667),
        },
        "Plateaux": {
            "Kloto": (6.9167, 0.6167),
            "Agou": (6.8500, 0.7833),
            "Danyi": (7.0000, 0.5000),
            "Kpélé": (7.1167, 1.0000),
            "Akébou": (7.5167, 1.1833),
            "Moyen-Mono": (7.3333, 1.2500),
            "Ogou": (7.7833, 1.5167),
        },
        "Centrale": {
            "Tchamba": (8.2167, 1.4167),
            "Sotouboua": (8.5667, 0.9833),
            "Tchaoudjo": (8.8833, 1.2667),
            "Blitta": (8.3333, 0.7667),
        },
        "Kara": {
            "Kozah": (9.5500, 1.1833),
            "Binah": (9.7000, 1.0667),
            "Bassar": (9.2500, 0.7833),
            "Dankpen": (9.8833, 1.3500),
            "Doufelgou": (9.7333, 0.4833),
        },
        "Savanes": {
            "Tandjouaré": (10.7833, 0.7833),
            "Tone": (11.0000, 0.3333),
            "Cinkassé": (11.1167, 0.3833),
            "Kpendjal": (10.9167, 1.0167),
        },
    },
    
    # Benin - Communes (major municipalities by department)
    "Benin": {
        "Littoral": {
            "Cotonou": (6.3654, 2.4183),
        },
        "Atlantique": {
            "Abomey-Calavi": (6.4500, 2.3500),
            "Allada": (6.6667, 2.1500),
            "Kpomassè": (6.3333, 2.1167),
            "Ouidah": (6.3578, 2.0889),
            "Sô-Ava": (6.4167, 2.4667),
            "Toffo": (6.5833, 2.0833),
            "Tori-Bossito": (6.5167, 1.9500),
            "Zè": (6.5000, 2.3333),
        },
        "Ouémé": {
            "Porto-Novo": (6.4969, 2.6289),
            "Aguégués": (6.5833, 2.4833),
            "Akpro-Missérété": (6.5500, 2.6833),
            "Avrankou": (6.4333, 2.8167),
            "Bonou": (6.9000, 2.4500),
            "Dangbo": (6.5833, 2.5333),
        },
        "Zou": {
            "Abomey": (7.1833, 1.9833),
            "Bohicon": (7.1833, 2.0667),
            "Cové": (7.2167, 2.2833),
            "Djidja": (7.3667, 1.9333),
            "Ouinhi": (7.0833, 2.4833),
            "Za-Kpota": (7.1333, 2.3333),
            "Zangnanado": (7.2833, 2.3500),
            "Zogbodomey": (7.1000, 2.2500),
        },
        "Borgou": {
            "Parakou": (9.3500, 2.6167),
            "Bembèrèkè": (10.2167, 2.6667),
            "Kalalé": (10.2833, 3.3833),
            "N'Dali": (9.8667, 2.7167),
            "Nikki": (9.9333, 3.2000),
            "Pèrèrè": (9.1833, 2.3667),
            "Sinendé": (10.0000, 2.4167),
            "Tchaourou": (8.8833, 2.5833),
        },
        "Mono": {
            "Lokossa": (6.6389, 1.7167),
            "Athiémé": (6.5667, 1.6667),
            "Bopa": (6.7833, 1.7833),
            "Comé": (6.4000, 1.8833),
            "Grand-Popo": (6.2833, 1.8167),
            "Houéyogbé": (6.5833, 1.8000),
        },
        "Atacora": {
            "Natitingou": (10.3000, 1.3833),
            "Boukoumbé": (10.1833, 1.1000),
            "Cobly": (10.3000, 1.0167),
            "Kérou": (10.8167, 1.9167),
            "Kouandé": (10.3333, 1.6833),
            "Matéri": (10.0667, 1.2667),
            "Péhunco": (10.1167, 1.5833),
            "Tanguiéta": (10.6167, 1.2667),
            "Toucountouna": (10.5833, 1.4000),
        },
    },
    
    # Cameroon - Divisions (major districts by region)
    "Cameroon": {
        "Centre": {
            "Mfoundi": (3.8480, 11.5021),  # Yaoundé
            "Mefou-et-Afamba": (3.7500, 11.7000),
            "Nyong-et-Kéllé": (3.5000, 12.0000),
            "Nyong-et-Mfoumou": (3.2000, 12.3000),
            "Nyong-et-So'o": (3.3333, 11.4167),
            "Mbam-et-Inoubou": (4.6000, 11.1667),
            "Mbam-et-Kim": (4.8333, 11.5000),
            "Méfou-et-Akono": (3.6167, 11.4000),
            "Lékié": (4.1000, 11.3500),
        },
        "Littoral": {
            "Wouri": (4.0511, 9.7679),  # Douala
            "Nkam": (4.6167, 9.9333),
            "Sanaga-Maritime": (3.5000, 9.8333),
            "Mungo": (4.6833, 9.4500),
        },
        "West": {
            "Bamboutos": (5.4667, 10.1000),
            "Haut-Nkam": (5.4667, 10.4833),
            "Hauts-Plateaux": (5.8333, 10.1667),
            "Koung-Khi": (5.8000, 10.5000),
            "Menoua": (5.5000, 10.3333),
            "Mifi": (5.4769, 10.4178),  # Bafoussam
            "Ndé": (5.1833, 10.7500),
            "Noun": (5.6667, 10.9000),
        },
        "Northwest": {
            "Mezam": (5.9667, 10.1500),  # Bamenda
            "Boyo": (6.2500, 10.2500),
            "Bui": (6.2833, 10.5000),
            "Donga-Mantung": (6.4167, 10.7833),
            "Menchum": (6.5833, 10.0500),
            "Momo": (6.1333, 9.8000),
            "Ngo-Ketunjia": (6.0833, 10.4167),
        },
        "Southwest": {
            "Fako": (4.1561, 9.2325),  # Limbe/Buea
            "Koupé-Manengouba": (4.8833, 9.8333),
            "Lebialem": (5.5000, 9.8333),
            "Manyu": (5.8000, 9.2500),
            "Meme": (4.9667, 9.0833),
            "Ndian": (4.7000, 8.7333),
        },
        "Far North": {
            "Diamaré": (10.5917, 14.2123),  # Maroua
            "Logone-et-Chari": (12.0833, 14.8333),
            "Mayo-Danay": (10.7500, 14.9167),
            "Mayo-Kani": (10.1667, 14.4167),
            "Mayo-Sava": (10.8333, 14.5833),
            "Mayo-Tsanaga": (10.8333, 13.8333),
        },
        "North": {
            "Bénoué": (8.9806, 13.3869),  # Garoua
            "Faro": (8.3500, 12.6333),
            "Mayo-Louti": (9.3000, 13.7333),
            "Mayo-Rey": (9.2000, 14.1667),
        },
        "Adamawa": {
            "Djérem": (6.4500, 14.1833),
            "Faro-et-Déo": (7.3697, 13.5844),  # Ngaoundéré
            "Mayo-Banyo": (6.7500, 11.8167),
            "Mbéré": (7.3667, 14.1833),
            "Vina": (7.2167, 13.5667),
        },
        "East": {
            "Haut-Nyong": (4.0000, 15.0000),
            "Kadey": (4.1667, 14.1667),
            "Lom-et-Djérem": (5.6667, 13.6667),
            "Boumba-et-Ngoko": (3.0000, 15.5000),
        },
        "South": {
            "Dja-et-Lobo": (3.2500, 12.7500),
            "Mvila": (2.5000, 11.5000),
            "Océan": (2.9261, 11.5214),  # Kribi
            "Vallée-du-Ntem": (2.1667, 10.5000),
        },
    },
}


def get_sub_divisions(country: str, division: str) -> List[str]:
    """Get list of sub-divisions (e.g., LGAs) for a specific division"""
    if country in AFRICA_SUB_DIVISIONS:
        if division in AFRICA_SUB_DIVISIONS[country]:
            return sorted(AFRICA_SUB_DIVISIONS[country][division].keys())
    return []


def get_sub_division_location(country: str, division: str, sub_division: str) -> Tuple[float, float]:
    """Get coordinates for a sub-division (e.g., LGA)"""
    if country in AFRICA_SUB_DIVISIONS:
        if division in AFRICA_SUB_DIVISIONS[country]:
            if sub_division in AFRICA_SUB_DIVISIONS[country][division]:
                return AFRICA_SUB_DIVISIONS[country][division][sub_division]
    return (0.0, 0.0)


def get_selected_locations(
    countries: List[str] = None, 
    divisions: Dict[str, List[str]] = None,
    sub_divisions: Dict[str, Dict[str, List[str]]] = None
) -> List[Tuple[float, float, str]]:
    """
    Get coordinates for selected countries, divisions, and sub-divisions
    
    Args:
        countries: List of country names (will use capital if no divisions specified)
        divisions: Dict of {country: [division names]}
        sub_divisions: Dict of {country: {division: [sub_division names]}}
    
    Returns:
        List of tuples: (latitude, longitude, location_name)
    """
    locations = []
    
    if sub_divisions:
        # Get specific sub-divisions (e.g., LGAs)
        for country, division_dict in sub_divisions.items():
            for division, sub_div_list in division_dict.items():
                for sub_div in sub_div_list:
                    lat, lon = get_sub_division_location(country, division, sub_div)
                    if lat != 0.0 or lon != 0.0:
                        locations.append((lat, lon, f"{sub_div}, {division}, {country}"))
    elif divisions:
        # Get specific divisions
        for country, division_list in divisions.items():
            for division in division_list:
                lat, lon = get_division_location(country, division)
                if lat != 0.0 or lon != 0.0:
                    locations.append((lat, lon, f"{division}, {country}"))
    elif countries:
        # Get capital cities for countries
        for country in countries:
            lat, lon = get_country_location(country)
            if lat != 0.0 or lon != 0.0:
                locations.append((lat, lon, f"{country} (Capital)"))
    
    return locations
