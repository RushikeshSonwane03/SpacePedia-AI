
import asyncio
import json
import os
import sys
import aiohttp # Added for search session

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ingestion.discovery import WikiDiscovery

# NODE 2: CATEGORY ONTOLOGY
ONTOLOGY = {
    "Space_Agencies": "Category:Space_agencies",
    "Commercial_Space": "Category:Spaceflight_companies",
    "Space_Missions": "Category:Space_missions",
    "Spacecraft_Engineering": "Category:Spacecraft",
    "Space_Stations": "Category:Space_stations",
    "Celestial_Objects": "Category:Celestial_objects",
    "Solar_System": "Category:Solar_System",
    "Astronomy_Cosmology": "Category:Astronomy",
    "Observatories": "Category:Observatories",
    "Earth_Observation": "Category:Earth_observation_satellites",
    "Space_Law": "Category:Space_law",
    "History_Spaceflight": "Category:History_of_spaceflight"
}

# NODE 6: FOUNDATIONAL TOPICS (Must Include)
FOUNDATIONAL_TOPICS = [
    "Sun", "Moon", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune",
    "Big Bang", "General relativity", "Black hole", "NASA", "SpaceX", 
    "Apollo 11", "International Space Station", "Hubble Space Telescope",
    "James Webb Space Telescope", "Solar System", "Galaxy", "Milky Way", "Universe"
]

# FIX 4: Commercial Space Queries
COMMERCIAL_QUERIES = [
    "commercial spaceflight",
    "private space company", 
    "space startup",
    "satellite operator",
    "SpaceX",
    "Blue Origin",
    "Rocket Lab",
    "Virgin Galactic"
]

def calculate_score(title: str, length: int) -> float:
    """
    NODE 4: PAGE SCORING + FIX 5 (Scoring remains same)
    """
    score = length / 1000.0  # 1 point per 1KB
    
    if title in FOUNDATIONAL_TOPICS:
        score += 100.0
    
    if "List of" in title:
        score -= 5.0
    if "timeline" in title.lower():
        score -= 2.0
        
    return score

async def main():
    discovery = WikiDiscovery()
    print("🌌 Starting Incremental Curation (Fix Layer Applied)...")
    
    categories = list(ONTOLOGY.values())
    raw_results = await discovery.discover_all(categories)
    
    # FIX 3: Commercial Space Fallback
    # If Category:Spaceflight_companies returned 0 (which it did), run search.
    comm_results = []
    async with aiohttp.ClientSession() as session:
        for q in COMMERCIAL_QUERIES:
            print(f"🔎 Searching '{q}' for Commercial Space...")
            res = await discovery.search_pages(session, q, limit=5)
            comm_results.extend(res)
    
    # Merge search results into the raw category bucket manually
    if "Category:Spaceflight_companies" not in raw_results:
        raw_results["Category:Spaceflight_companies"] = []
    
    # Deduplicate search results
    seen_urls = set(p[1] for p in raw_results["Category:Spaceflight_companies"])
    for p in comm_results:
        if p[1] not in seen_urls:
            raw_results["Category:Spaceflight_companies"].append(p)
            seen_urls.add(p[1])


    curated_data = {}
    total_selected = 0
    
    for category_name, wiki_cat in ONTOLOGY.items():
        pages = raw_results.get(wiki_cat, [])
        scored_pages = []
        
        # Scored List
        for title, url, length in pages:
            score = calculate_score(title, length)
            
            # FIX 2: Virtual Tagging for Celestial Objects
            tags = [category_name]
            # Heuristic: If it's in Solar System or Astronomy AND is a physical object
            # For simplicity, we tag FOUNDATIONAL objects + simple heuristic
            is_celestial = category_name in ["Solar_System", "Astronomy_Cosmology"] and (
                title in FOUNDATIONAL_TOPICS or "Star" in title or "Planet" in title or "Galaxy" in title
            )
            if is_celestial:
                tags.append("Celestial_Objects")

            scored_pages.append({
                "title": title,
                "url": url,
                "length": length,
                "score": score,
                "category": category_name,
                "tags": tags, # New semantic tags
                "selected": True
            })
            
        # FIX 1: Anchor Page for Celestial Objects
        if category_name == "Celestial_Objects":
            # Explicitly add "Astronomical object" if not present
            if not any(p['title'] == "Astronomical object" for p in scored_pages):
                # We need to fetch it? Or just assume? 
                # Let's mock a fetch or assume standard URL. 
                # Better: Use discovery to get it real quick?
                # For safety/speed, we'll hardcode one high-value anchor.
                scored_pages.append({
                    "title": "Astronomical object",
                    "url": "https://en.wikipedia.org/wiki/Astronomical_object",
                    "length": 50000, # Approx placeholder
                    "score": 150.0, # High score anchor
                    "category": "Celestial_Objects",
                    "tags": ["Celestial_Objects", "Astronomy_Cosmology"],
                    "selected": True
                })

        # Sort by Score DESC
        scored_pages.sort(key=lambda x: x["score"], reverse=True)
        
        # FIX 4: Soft Normalization (Top 25)
        top_n = scored_pages[:25]
        
        # Foundational Rescue
        existing_titles = {p['title'] for p in top_n}
        for p in scored_pages[25:]:
            if p['score'] > 90 and p['title'] not in existing_titles:
                 top_n.append(p)
        
        curated_data[category_name] = top_n
        total_selected += len(top_n)
        
        print(f"✅ {category_name}: Selected {len(top_n)} pages")

    output_file = "app/ingestion/candidates.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(curated_data, f, indent=2)
        
    print("-" * 50)
    print(f"🚀 Incremental Curation Complete! Identified {total_selected} pages.")
    print("Commercial_Space & Celestial_Objects should now be populated.")

if __name__ == "__main__":
    asyncio.run(main())
