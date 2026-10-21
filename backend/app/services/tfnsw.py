import json

async def fetch_tfnsw_trip(origin: str, destination: str, time: str) -> str:
    """
    Mock TfNSW API response.
    Later, this will use `httpx` to call the real opendata.transport.nsw.gov.au endpoint.
    """
    print(f"\n[BACKEND EXECUTING API] Fetching route: {origin} -> {destination} at {time}...")
    
    return json.dumps({
        "status": "success",
        "route": "T1 North Shore Line",
        "departure_time": "09:04 AM",
        "arrival_time": "09:22 AM",
        "platform": "Platform 16",
        "duration_minutes": 18,
        "delays": "None"
    })