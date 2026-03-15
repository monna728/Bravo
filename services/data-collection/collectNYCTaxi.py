import json
import boto3
import requests
from datetime import datetime, timezone

NYC_TLC_API = "https://data.cityofnewyork.us/resource/4b4i-vvec.json"
# replace with bucket from AWS
S3_BUCKET   = "bucket-placeholder"
# replace with path inside bucket
S3_KEY      = "tlc/raw/tlc_trips.json"
# 1000 for now
LIMIT       = 1000
TIMEZONE    = "America/New_York"

ZONE_LOOKUP = {
    1:   ("EWR",          "Newark Airport"),
    2:   ("Queens",       "Jamaica Bay"),
    3:   ("Bronx",        "Allerton/Pelham Gardens"),
    4:   ("Manhattan",    "Alphabet City"),
    5:   ("Staten Island","Arden Heights"),
    6:   ("Staten Island","Arrochar/Fort Wadsworth"),
    7:   ("Queens",       "Astoria"),
    8:   ("Queens",       "Astoria Park"),
    9:   ("Queens",       "Auburndale"),
    10:  ("Queens",       "Baisley Park"),
    11:  ("Brooklyn",     "Bath Beach"),
    12:  ("Manhattan",    "Battery Park"),
    13:  ("Manhattan",    "Battery Park City"),
    14:  ("Brooklyn",     "Bay Ridge"),
    15:  ("Queens",       "Bay Terrace/Fort Totten"),
    16:  ("Queens",       "Bayside"),
    17:  ("Brooklyn",     "Bedford"),
    18:  ("Bronx",        "Bedford Park"),
    19:  ("Queens",       "Bellerose"),
    20:  ("Bronx",        "Belmont"),
    21:  ("Brooklyn",     "Bensonhurst East"),
    22:  ("Brooklyn",     "Bensonhurst West"),
    23:  ("Staten Island","Bloomfield/Emerson Hill"),
    24:  ("Manhattan",    "Bloomingdale"),
    25:  ("Brooklyn",     "Boerum Hill"),
    26:  ("Brooklyn",     "Borough Park"),
    27:  ("Queens",       "Breezy Point/Fort Tilden/Riis Beach"),
    28:  ("Queens",       "Briarwood/Jamaica Hills"),
    29:  ("Brooklyn",     "Brighton Beach"),
    30:  ("Queens",       "Broad Channel"),
    31:  ("Bronx",        "Bronx Park"),
    32:  ("Bronx",        "Bronxdale"),
    33:  ("Brooklyn",     "Brooklyn Heights"),
    34:  ("Brooklyn",     "Brooklyn Navy Yard"),
    35:  ("Brooklyn",     "Brownsville"),
    36:  ("Brooklyn",     "Bushwick North"),
    37:  ("Brooklyn",     "Bushwick South"),
    38:  ("Queens",       "Cambria Heights"),
    39:  ("Brooklyn",     "Canarsie"),
    40:  ("Brooklyn",     "Carroll Gardens"),
    41:  ("Manhattan",    "Central Harlem"),
    42:  ("Manhattan",    "Central Harlem North"),
    43:  ("Manhattan",    "Central Park"),
    44:  ("Staten Island","Charleston/Tottenville"),
    45:  ("Manhattan",    "Chinatown"),
    46:  ("Bronx",        "City Island"),
    47:  ("Bronx",        "Claremont/Bathgate"),
    48:  ("Manhattan",    "Clinton East"),
    49:  ("Brooklyn",     "Clinton Hill"),
    50:  ("Manhattan",    "Clinton West"),
    51:  ("Bronx",        "Co-Op City"),
    52:  ("Brooklyn",     "Cobble Hill"),
    53:  ("Queens",       "College Point"),
    54:  ("Brooklyn",     "Columbia Street"),
    55:  ("Brooklyn",     "Coney Island"),
    56:  ("Queens",       "Corona"),
    57:  ("Queens",       "Corona"),
    58:  ("Bronx",        "Country Club"),
    59:  ("Bronx",        "Crotona Park"),
    60:  ("Bronx",        "Crotona Park East"),
    61:  ("Brooklyn",     "Crown Heights North"),
    62:  ("Brooklyn",     "Crown Heights South"),
    63:  ("Brooklyn",     "Cypress Hills"),
    64:  ("Queens",       "Douglaston"),
    65:  ("Brooklyn",     "Downtown Brooklyn/MetroTech"),
    66:  ("Brooklyn",     "DUMBO/Vinegar Hill"),
    67:  ("Brooklyn",     "Dyker Heights"),
    68:  ("Manhattan",    "East Chelsea"),
    69:  ("Bronx",        "East Concourse/Concourse Village"),
    70:  ("Queens",       "East Elmhurst"),
    71:  ("Brooklyn",     "East Flatbush/Farragut"),
    72:  ("Brooklyn",     "East Flatbush/Remsen Village"),
    73:  ("Queens",       "East Flushing"),
    74:  ("Manhattan",    "East Harlem North"),
    75:  ("Manhattan",    "East Harlem South"),
    76:  ("Brooklyn",     "East New York"),
    77:  ("Brooklyn",     "East New York/Pennsylvania Avenue"),
    78:  ("Bronx",        "East Tremont"),
    79:  ("Manhattan",    "East Village"),
    80:  ("Brooklyn",     "East Williamsburg"),
    81:  ("Bronx",        "Eastchester"),
    82:  ("Queens",       "Elmhurst"),
    83:  ("Queens",       "Elmhurst/Maspeth"),
    84:  ("Staten Island","Eltingville/Annadale/Prince's Bay"),
    85:  ("Brooklyn",     "Erasmus"),
    86:  ("Queens",       "Far Rockaway"),
    87:  ("Manhattan",    "Financial District North"),
    88:  ("Manhattan",    "Financial District South"),
    89:  ("Brooklyn",     "Flatbush/Ditmas Park"),
    90:  ("Manhattan",    "Flatiron"),
    91:  ("Brooklyn",     "Flatlands"),
    92:  ("Queens",       "Flushing"),
    93:  ("Queens",       "Flushing Meadows-Corona Park"),
    94:  ("Bronx",        "Fordham South"),
    95:  ("Queens",       "Forest Hills"),
    96:  ("Queens",       "Forest Park/Highland Park"),
    97:  ("Brooklyn",     "Fort Greene"),
    98:  ("Queens",       "Fresh Meadows"),
    99:  ("Staten Island","Freshkills Park"),
    100: ("Manhattan",    "Garment District"),
    101: ("Queens",       "Glen Oaks"),
    102: ("Queens",       "Glendale"),
    103: ("Manhattan",    "Governor's Island/Ellis Island/Liberty Island"),
    104: ("Manhattan",    "Governor's Island/Ellis Island/Liberty Island"),
    105: ("Manhattan",    "Governor's Island/Ellis Island/Liberty Island"),
    106: ("Brooklyn",     "Gowanus"),
    107: ("Manhattan",    "Gramercy"),
    108: ("Brooklyn",     "Gravesend"),
    109: ("Staten Island","Great Kills"),
    110: ("Staten Island","Great Kills Park"),
    111: ("Brooklyn",     "Green-Wood Cemetery"),
    112: ("Brooklyn",     "Greenpoint"),
    113: ("Manhattan",    "Greenwich Village North"),
    114: ("Manhattan",    "Greenwich Village South"),
    115: ("Staten Island","Grymes Hill/Clifton"),
    116: ("Manhattan",    "Hamilton Heights"),
    117: ("Queens",       "Hammels/Arverne"),
    118: ("Staten Island","Heartland Village/Todt Hill"),
    119: ("Bronx",        "Highbridge"),
    120: ("Manhattan",    "Highbridge Park"),
    121: ("Queens",       "Hillcrest/Pomonok"),
    122: ("Queens",       "Hollis"),
    123: ("Brooklyn",     "Homecrest"),
    124: ("Queens",       "Howard Beach"),
    125: ("Manhattan",    "Hudson Sq"),
    126: ("Bronx",        "Hunts Point"),
    127: ("Manhattan",    "Inwood"),
    128: ("Manhattan",    "Inwood Hill Park"),
    129: ("Queens",       "Jackson Heights"),
    130: ("Queens",       "Jamaica"),
    131: ("Queens",       "Jamaica Estates"),
    132: ("Queens",       "JFK Airport"),
    133: ("Brooklyn",     "Kensington"),
    134: ("Queens",       "Kew Gardens"),
    135: ("Queens",       "Kew Gardens Hills"),
    136: ("Bronx",        "Kingsbridge Heights"),
    137: ("Manhattan",    "Kips Bay"),
    138: ("Queens",       "LaGuardia Airport"),
    139: ("Queens",       "Laurelton"),
    140: ("Manhattan",    "Lenox Hill East"),
    141: ("Manhattan",    "Lenox Hill West"),
    142: ("Manhattan",    "Lincoln Square East"),
    143: ("Manhattan",    "Lincoln Square West"),
    144: ("Manhattan",    "Little Italy/NoLiTa"),
    145: ("Queens",       "Long Island City/Hunters Point"),
    146: ("Queens",       "Long Island City/Queens Plaza"),
    147: ("Bronx",        "Longwood"),
    148: ("Manhattan",    "Lower East Side"),
    149: ("Brooklyn",     "Madison"),
    150: ("Brooklyn",     "Manhattan Beach"),
    151: ("Manhattan",    "Manhattan Valley"),
    152: ("Manhattan",    "Manhattanville"),
    153: ("Manhattan",    "Marble Hill"),
    154: ("Brooklyn",     "Marine Park/Floyd Bennett Field"),
    155: ("Brooklyn",     "Marine Park/Mill Basin"),
    156: ("Staten Island","Mariners Harbor"),
    157: ("Queens",       "Maspeth"),
    158: ("Manhattan",    "Meatpacking/West Village West"),
    159: ("Bronx",        "Melrose South"),
    160: ("Queens",       "Middle Village"),
    161: ("Manhattan",    "Midtown Center"),
    162: ("Manhattan",    "Midtown East"),
    163: ("Manhattan",    "Midtown North"),
    164: ("Manhattan",    "Midtown South"),
    165: ("Brooklyn",     "Midwood"),
    166: ("Manhattan",    "Morningside Heights"),
    167: ("Bronx",        "Morrisania/Melrose"),
    168: ("Bronx",        "Mott Haven/Port Morris"),
    169: ("Bronx",        "Mount Hope"),
    170: ("Manhattan",    "Murray Hill"),
    171: ("Queens",       "Murray Hill-Queens"),
    172: ("Staten Island","New Dorp/Midland Beach"),
    173: ("Queens",       "North Corona"),
    174: ("Bronx",        "Norwood"),
    175: ("Queens",       "Oakland Gardens"),
    176: ("Staten Island","Oakwood"),
    177: ("Brooklyn",     "Ocean Hill"),
    178: ("Brooklyn",     "Ocean Parkway South"),
    179: ("Queens",       "Old Astoria"),
    180: ("Queens",       "Ozone Park"),
    181: ("Brooklyn",     "Park Slope"),
    182: ("Bronx",        "Parkchester"),
    183: ("Bronx",        "Pelham Bay"),
    184: ("Bronx",        "Pelham Bay Park"),
    185: ("Bronx",        "Pelham Parkway"),
    186: ("Manhattan",    "Penn Station/Madison Sq West"),
    187: ("Staten Island","Port Richmond"),
    188: ("Brooklyn",     "Prospect-Lefferts Gardens"),
    189: ("Brooklyn",     "Prospect Heights"),
    190: ("Brooklyn",     "Prospect Park"),
    191: ("Queens",       "Queens Village"),
    192: ("Queens",       "Queensboro Hill"),
    193: ("Queens",       "Queensbridge/Ravenswood"),
    194: ("Manhattan",    "Randalls Island"),
    195: ("Brooklyn",     "Red Hook"),
    196: ("Queens",       "Rego Park"),
    197: ("Queens",       "Richmond Hill"),
    198: ("Queens",       "Ridgewood"),
    199: ("Bronx",        "Rikers Island"),
    200: ("Bronx",        "Riverdale/North Riverdale/Fieldston"),
    201: ("Queens",       "Rockaway Park"),
    202: ("Manhattan",    "Roosevelt Island"),
    203: ("Queens",       "Rosedale"),
    204: ("Staten Island","Rossville/Woodrow"),
    205: ("Queens",       "Saint Albans"),
    206: ("Staten Island","Saint George/New Brighton"),
    207: ("Queens",       "Saint Michaels Cemetery/Woodside"),
    208: ("Bronx",        "Schuylerville/Edgewater Park"),
    209: ("Manhattan",    "Seaport"),
    210: ("Brooklyn",     "Sheepshead Bay"),
    211: ("Manhattan",    "SoHo"),
    212: ("Bronx",        "Soundview/Bruckner"),
    213: ("Bronx",        "Soundview/Castle Hill"),
    214: ("Staten Island","South Beach/Dongan Hills"),
    215: ("Queens",       "South Jamaica"),
    216: ("Queens",       "South Ozone Park"),
    217: ("Brooklyn",     "South Williamsburg"),
    218: ("Queens",       "Springfield Gardens North"),
    219: ("Queens",       "Springfield Gardens South"),
    220: ("Bronx",        "Spuyten Duyvil/Kingsbridge"),
    221: ("Staten Island","Stapleton"),
    222: ("Brooklyn",     "Starrett City"),
    223: ("Queens",       "Steinway"),
    224: ("Manhattan",    "Stuy Town/Peter Cooper Village"),
    225: ("Brooklyn",     "Stuyvesant Heights"),
    226: ("Queens",       "Sunnyside"),
    227: ("Brooklyn",     "Sunset Park East"),
    228: ("Brooklyn",     "Sunset Park West"),
    229: ("Manhattan",    "Sutton Place/Turtle Bay North"),
    230: ("Manhattan",    "Times Sq/Theatre District"),
    231: ("Manhattan",    "TriBeCa/Civic Center"),
    232: ("Manhattan",    "Two Bridges/Seward Park"),
    233: ("Manhattan",    "UN/Turtle Bay South"),
    234: ("Manhattan",    "Union Sq"),
    235: ("Bronx",        "University Heights/Morris Heights"),
    236: ("Manhattan",    "Upper East Side North"),
    237: ("Manhattan",    "Upper East Side South"),
    238: ("Manhattan",    "Upper West Side North"),
    239: ("Manhattan",    "Upper West Side South"),
    240: ("Bronx",        "Van Cortlandt Park"),
    241: ("Bronx",        "Van Cortlandt Village"),
    242: ("Bronx",        "Van Nest/Morris Park"),
    243: ("Manhattan",    "Washington Heights North"),
    244: ("Manhattan",    "Washington Heights South"),
    245: ("Staten Island","West Brighton"),
    246: ("Manhattan",    "West Chelsea/Hudson Yards"),
    247: ("Bronx",        "West Concourse"),
    248: ("Bronx",        "West Farms/Bronx River"),
    249: ("Manhattan",    "West Village"),
    250: ("Bronx",        "Westchester Village/Unionport"),
    251: ("Staten Island","Westerleigh"),
    252: ("Queens",       "Whitestone"),
    253: ("Queens",       "Willets Point"),
    254: ("Bronx",        "Williamsbridge/Olinville"),
    255: ("Brooklyn",     "Williamsburg (North Side)"),
    256: ("Brooklyn",     "Williamsburg (South Side)"),
    257: ("Brooklyn",     "Windsor Terrace"),
    258: ("Queens",       "Woodhaven"),
    259: ("Bronx",        "Woodlawn/Wakefield"),
    260: ("Queens",       "Woodside"),
    261: ("Manhattan",    "World Trade Center"),
    262: ("Manhattan",    "Yorkville East"),
    263: ("Manhattan",    "Yorkville West"),
    264: ("Unknown",      "N/A"),
    265: ("N/A",          "Outside of NYC"),
}

def fetch_tlc_data(limit=LIMIT):
    params = {"$limit": limit, "$order": "tpep_pickup_datetime DESC"}
    response = requests.get(NYC_TLC_API, params=params, timeout=30)
    response.raise_for_status()
    return response.json()

def calculate_duration_minutes(pickup_str, dropoff_str):
    fmt = "%Y-%m-%dT%H:%M:%S.%f"
    try:
        pickup  = datetime.strptime(pickup_str, fmt)
        dropoff = datetime.strptime(dropoff_str, fmt)
        return round((dropoff - pickup).total_seconds() / 60, 2)
    except Exception:
        return 0
    
def locationid_to_zone(location_id: int):
    """
    Takes an integer location ID and returns a tuple of (borough, zone).
    Falls back to ("Unknown", "Unknown") if the ID isn't in the lookup.
    """
    return ZONE_LOOKUP.get(location_id, ("Unknown", "Unknown"))

# convert raw NYC TLC records into the ADAGE 3.0 data model format and each taxi trip becomes one 'event' in the events array
def transform_to_adage(raw_records):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    adage_output = {
        "data_source": "nyc_tlc",
        "dataset_type": "taxi_trips",
        "dataset_id": f"s3://{S3_BUCKET}/{S3_KEY}",
        "time_object": {
            "timestamp": now,
            "timezone": TIMEZONE
        },
        "events": []
    }

    for record in raw_records:
        pickup_time  = record.get("tpep_pickup_datetime", "")
        dropoff_time = record.get("tpep_dropoff_datetime", "")
        duration_min = calculate_duration_minutes(pickup_time, dropoff_time)
        pickup_formatted = pickup_time.replace("T", " ").replace(".000", ".000000")

        pu_id = int(record.get("pulocationid",0))
        do_id = int(record.get("dolocationid",0))

        pu_zone, pu_borough = locationid_to_zone(pu_id)
        do_zone, do_borough = locationid_to_zone(do_id)


        event = {
            "time_object": {
                "timestamp":     pickup_formatted,
                "duration":      duration_min,
                "duration_unit": "minute",
                "timezone":      TIMEZONE
            },
            "event_type": "taxi_pickup",
            "attribute": {
                "vendorid":           int(record.get("vendorid", 0)),
                "pickup_locationid":  pu_id,
                "pickup_zone":        pu_zone,
                "pickup_borough":         pu_borough,
                "dropoff_locationid": do_id,
                "dropoff_zone":       do_zone,
                "dropoff_borough":    do_borough,
                "passenger_count":    float(record.get("passenger_count", 0)),
                "trip_distance":      float(record.get("trip_distance", 0)),
                "fare_amount":        float(record.get("fare_amount", 0)),
                "total_amount":       float(record.get("total_amount", 0)),
                "payment_type":       int(record.get("payment_type", 0)),
                "congestion_surcharge": float(record.get("congestion_surcharge", 0)),
                "ratecodeid":         float(record.get("ratecodeid", 1))
            }
        }
        adage_output["events"].append(event)

    return adage_output

# def locationid_to_borough(locationId):
#     borough_name = ""
#     return borough_name


def save_to_s3(data: dict, bucket: str, key: str):
    # save a Python dict as a JSON file to S3 bucket
    s3_client = boto3.client("s3")
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data, indent=2),
        ContentType="application/json"
    )
    print(f"✅ Saved to s3://{bucket}/{key}")

# not running yet - running locally first
# AWS Lambda entry point
# called automatically by AWS when triggered
def lambda_handler(event, context):
    print("Starting TLC data collection...")

    raw_records = fetch_tlc_data(limit=LIMIT)
    print(f"Fetched {len(raw_records)} records from NYC TLC API")

    adage_data = transform_to_adage(raw_records)
    print(f"Transformed {len(adage_data['events'])} events into ADAGE format")

    save_to_s3(adage_data, S3_BUCKET, S3_KEY)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Data collection complete",
            "records_collected": len(adage_data["events"]),
            "s3_location": f"s3://{S3_BUCKET}/{S3_KEY}"
        })
    }


# locally testing before using AWS S3 bucket
if __name__ == "__main__":
    import json

    # 50 records for now for local testing
    raw_records = fetch_tlc_data(limit=50)
    print(f"Fetched {len(raw_records)} records")

    adage_data = transform_to_adage(raw_records)
    print(f"Transformed {len(adage_data['events'])} events")

    # creating test output file for local testing
    with open("test_output.json", "w") as f:
        json.dump(adage_data, f, indent=2)
    print("Output saved to test_output.json")