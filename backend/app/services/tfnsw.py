import os
import json
import httpx
from datetime import datetime
import pytz

TFNSW_API_KEY = os.getenv("TFNSW_API_KEY")

def format_iso_time(iso_str: str) -> str:
    """Converts TfNSW UTC ISO time ('2026-11-05T01:04:00Z') to Sydney time ('12:04 PM')."""
    if not iso_str: 
        return "Unknown"
    try:
        # Parse the raw UTC time
        dt_utc = datetime.strptime(iso_str, "%Y-%m-%dT%H:%M:%SZ")
        dt_utc = dt_utc.replace(tzinfo=pytz.UTC)
        
        # Convert to Sydney timezone
        sydney_tz = pytz.timezone('Australia/Sydney')
        dt_syd = dt_utc.astimezone(sydney_tz)
        
        return dt_syd.strftime("%I:%M %p")
    except Exception:
        return iso_str

async def get_location_id(client: httpx.AsyncClient, headers: dict, location_name: str) -> str:
    url = "https://api.transport.nsw.gov.au/v1/tp/stop_finder"
    params = {
        "outputFormat": "rapidJSON",
        "type_sf": "any",
        "name_sf": location_name,
        "coordOutputFormat": "EPSG:4326"
    }
    try:
        response = await client.get(url, headers=headers, params=params, timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            locations = data.get("locations", [])
            if locations:
                return locations[0]["id"]
    except Exception as e:
        print(f"Stop finder failed: {e}")
    return location_name

async def fetch_tfnsw_trip(origin: str, destination: str, time: str) -> str:
    if not TFNSW_API_KEY:
        return json.dumps({"error": "TFNSW_API_KEY is not set in the environment."})
        
    sydney_tz = pytz.timezone('Australia/Sydney')
    now = datetime.now(sydney_tz)
    
    time_formatted = now.strftime("%H%M")
    if time and time.lower() != "now":
        try:
            if "AM" in time.upper() or "PM" in time.upper():
                time_formatted = datetime.strptime(time.strip(), "%I:%M %p").strftime("%H%M")
            elif ":" in time:
                time_formatted = datetime.strptime(time.strip(), "%H:%M").strftime("%H%M")
        except ValueError:
            pass
            
    date_formatted = now.strftime("%Y%m%d")
    print(f"\n[BACKEND EXECUTING API] Fetching live route: {origin} -> {destination} at {time_formatted}...")

    headers = {
        "Authorization": f"apikey {TFNSW_API_KEY}",
        "Accept": "application/json"
    }

    async with httpx.AsyncClient() as client:
        try:
            origin_id = await get_location_id(client, headers, origin)
            dest_id = await get_location_id(client, headers, destination)
            
            url = "https://api.transport.nsw.gov.au/v1/tp/trip"
            params = {
                "outputFormat": "rapidJSON",
                "coordOutputFormat": "EPSG:4326",
                "depArrMacro": "dep",
                "itdDate": date_formatted,
                "itdTime": time_formatted,
                "type_origin": "any",
                "name_origin": origin_id,
                "type_destination": "any",
                "name_destination": dest_id,
                "calcNumberOfTrips": 6,
                "includedMeans": "checkbox",
                "inclMOT_1": "on",
                "inclMOT_4": "off",
                "inclMOT_5": "off",
                "inclMOT_7": "off",
                "inclMOT_9": "off",
                "inclMOT_11": "off",
                "changeSpeed": "fast"
            }

            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            print(f"TFNSW RAW RESPONSE: {json.dumps(data)[:2000]}")
            
            journeys = data.get("journeys", [])
            if not journeys:
                return json.dumps({"error": f"No routes found from {origin} to {destination}."})
                
            trip_options = []
            
            for journey in journeys:
                if len(trip_options) >= 3:
                    break 
                    
                legs = journey.get("legs", [])
                
                active_legs = [leg for leg in legs if "walk" not in leg.get("transportation", {}).get("name", "Walk").lower()]
                if not active_legs:
                    active_legs = legs
                
                # Check if trip is in the past, allow 1 minute grace period
                first_leg_dep = active_legs[0].get("origin", {}).get("departureTimeEstimated", active_legs[0].get("origin", {}).get("departureTimePlanned"))
                try:
                    from datetime import timedelta
                    dt_utc = datetime.strptime(first_leg_dep, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
                    
                    # If it departed more than 1 minute ago, filter it out
                    if dt_utc < datetime.now(pytz.UTC) - timedelta(minutes=1):
                        continue 
                except Exception:
                    pass 
                
                route_summary = []
                for leg in active_legs:
                    transport_mode = leg.get("transportation", {}).get("name", "Unknown")
                    origin_node = leg.get("origin", {})
                    dest_node = leg.get("destination", {})
                    
                    dep_raw = origin_node.get("departureTimeEstimated", origin_node.get("departureTimePlanned"))
                    arr_raw = dest_node.get("arrivalTimeEstimated", dest_node.get("arrivalTimePlanned"))
                    
                    origin_name = origin_node.get("name", "Unknown").split(",")[0]
                    dest_name = dest_node.get("name", "Unknown").split(",")[0]
                    
                    origin_platform = origin_node.get("properties", {}).get("platformName")
                    dest_platform = dest_node.get("properties", {}).get("platformName")
                    
                    if origin_platform:
                        origin_name = f"{origin_name}, {origin_platform}"
                    if dest_platform:
                        dest_name = f"{dest_name}, {dest_platform}"

                    route_summary.append({
                        "train": transport_mode,
                        "departing": origin_name,
                        "departure_time": format_iso_time(dep_raw),
                        "arriving": dest_name,
                        "arrival_time": format_iso_time(arr_raw)
                    })
                
                trip_options.append({
                    "option": len(trip_options) + 1,
                    "duration_minutes": journey.get("duration", 0),
                    "legs": route_summary
                })
                
            if not trip_options:
                return json.dumps({"error": "No upcoming routes found. Please ask the user to specify a later departure time."})
            
            return json.dumps({
                "status": "success",
                "trips": trip_options
            })
            
        except Exception as e:
            return json.dumps({"error": f"Internal fetch error: {e}"})