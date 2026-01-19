
import aiohttp
import asyncio
from typing import List, Tuple, Dict
from urllib.parse import quote

class WikiDiscovery:
    """Discovery service to find Wikipedia pages by Category."""
    
    BASE_API = "https://en.wikipedia.org/w/api.php"
    
    def __init__(self):
        # Wikipedia requires a User-Agent with contact info to avoid blocking (403)
        self.headers = {
            "User-Agent": "SpacePediaAI/1.0 (https://github.com/example/spacepedia; spacepedia_bot@example.com)"
        }

    async def fetch_category_members(self, session: aiohttp.ClientSession, category: str, limit: int = 500) -> List[Tuple[str, str]]:
        """
        Fetches page titles and URLs for a given Wikipedia category.
        Returns a list of tuples: (Title, FullURL)
        """
        # Ensure category starts with 'Category:'
        if not category.startswith("Category:"):
            category = f"Category:{category}"
            
        params = {
            "action": "query",
            "generator": "categorymembers",
            "gcmtitle": category,
            "gcmlimit": limit,
            "gcmtype": "page", 
            "prop": "info|pageprops", # Fetch size/info
            "format": "json"
        }
        
        try:
            async with session.get(self.BASE_API, params=params, headers=self.headers) as resp:
                if resp.status != 200:
                    print(f"Error fetching category {category}: {resp.status}")
                    return []
                
                data = await resp.json()
                pages = data.get("query", {}).get("pages", {})
                
                results = []
                for pid, p in pages.items():
                    title = p['title']
                    length = p.get('length', 0)
                    
                    # Construct URL
                    url_slug = quote(title.replace(" ", "_"))
                    url = f"https://en.wikipedia.org/wiki/{url_slug}"
                    
                    # Store (Title, URL, Length)
                    results.append((title, url, length))
                    
                return results
                
        except Exception as e:
            print(f"Exception fetching {category}: {e}")
            return []

    async def discover_all(self, categories: List[str]) -> Dict[str, List[Tuple[str, str, int]]]:
        """
        Discover pages for multiple categories.
        Returns Dict[CategoryName -> List[(Title, URL, Length)]]
        """
        results = {}
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_category_members(session, cat) for cat in categories]
            # Gather maintains order of tasks
            lists = await asyncio.gather(*tasks)
            
            for cat, member_list in zip(categories, lists):
                results[cat] = member_list
                
        return results

    async def search_pages(self, session: aiohttp.ClientSession, query: str, limit: int = 15) -> List[Tuple[str, str, int]]:
        """
        Search Wikipedia for a query string.
        Returns List[(Title, URL, Length)]
        """
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": query,
            "gsrlimit": limit,
            "prop": "info|pageprops", 
            "format": "json"
        }
        
        try:
            async with session.get(self.BASE_API, params=params, headers=self.headers) as resp:
                if resp.status != 200:
                    print(f"Error searching {query}: {resp.status}")
                    return []
                
                data = await resp.json()
                pages = data.get("query", {}).get("pages", {})
                
                results = []
                for pid, p in pages.items():
                    title = p['title']
                    length = p.get('length', 0)
                    
                    # Construct URL
                    url_slug = quote(title.replace(" ", "_"))
                    url = f"https://en.wikipedia.org/wiki/{url_slug}"
                    
                    results.append((title, url, length))
                    
                return results
                
        except Exception as e:
            print(f"Exception searching {query}: {e}")
            return []
