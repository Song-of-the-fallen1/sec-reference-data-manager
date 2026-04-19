"""
SEC Reference Data Manager
Manages SEC reference data including CIK to ticker mappings and company metadata.
Downloads and parses SEC's public JSON files - no API key required.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Optional, List
from datetime import datetime
import os

class SECReferenceDataManager:
    """
    Manages SEC reference data.
    Data sources:
    - https://www.sec.gov/files/company_tickers.json
    - https://www.sec.gov/files/company_tickers_exchange.json
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """
        Initialize the reference data manager.
        
        Args:
            cache_dir: Directory to store cached JSON files
        """
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        
        # SEC data URLs
        self.company_tickers_url = "https://www.sec.gov/files/company_tickers.json"
        self.company_tickers_exchange_url = "https://www.sec.gov/files/company_tickers_exchange.json"
        
        # User agent required by SEC
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; ResearchBot/1.0)'
        }
        
        # Data stores
        self.cik_to_ticker = {}
        self.ticker_to_cik = {}
        self.cik_to_name = {}
        self.ticker_to_name = {}
        self.exchange_data = {}
        
        # Load data on initialization
        self.load_all_data()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _fetch_json(self, url: str, cache_filename: str) -> Optional[Dict]:
        """
        Fetch JSON from URL with caching.
        
        Args:
            url: URL to fetch
            cache_filename: Filename for cache
            
        Returns:
            Parsed JSON or None if failed
        """
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        # Check if cache exists and is less than 24 hours old
        if os.path.exists(cache_path):
            cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(cache_path))
            if cache_age.total_seconds() < 86400:  # 24 hours
                with open(cache_path, 'r') as f:
                    return json.load(f)
        
        # Fetch from SEC
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                # Save to cache
                with open(cache_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                return data
        except urllib.error.URLError as e:
            print(f"Error fetching {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {url}: {e}")
            return None
    
    def load_company_tickers(self):
        """
        Load company tickers from SEC.
        Data format: {"0": {"cik": 320193, "name": "Apple Inc.", "ticker": "AAPL"}}
        """
        data = self._fetch_json(self.company_tickers_url, "company_tickers.json")
        
        if not data:
            print("Failed to load company tickers data")
            return
        
        for key, value in data.items():
            cik = str(value.get('cik', '')).zfill(10)
            ticker = value.get('ticker', '')
            name = value.get('title', '')
            
            if cik and ticker:
                self.cik_to_ticker[cik] = ticker
                self.ticker_to_cik[ticker.upper()] = cik
                self.cik_to_name[cik] = name
                self.ticker_to_name[ticker.upper()] = name
        
        print(f"Loaded {len(self.cik_to_ticker)} company ticker mappings")
    
    def load_exchange_tickers(self):
        """
        Load exchange tickers from SEC (includes more detailed data).
        Data format: {"fields": ["cik", "name", "ticker", "exchange"], "data": [...]}
        """
        data = self._fetch_json(self.company_tickers_exchange_url, "company_tickers_exchange.json")
        
        if not data:
            print("Failed to load exchange tickers data")
            return
        
        fields = data.get('fields', [])
        data_rows = data.get('data', [])
        
        # Find field indices
        cik_idx = fields.index('cik') if 'cik' in fields else None
        name_idx = fields.index('name') if 'name' in fields else None
        ticker_idx = fields.index('ticker') if 'ticker' in fields else None
        exchange_idx = fields.index('exchange') if 'exchange' in fields else None
        
        for row in data_rows:
            if cik_idx is not None and ticker_idx is not None:
                cik = str(row[cik_idx]).zfill(10)
                ticker = row[ticker_idx]
                name = row[name_idx] if name_idx is not None else ''
                exchange = row[exchange_idx] if exchange_idx is not None else ''
                
                self.cik_to_ticker[cik] = ticker
                self.ticker_to_cik[ticker.upper()] = cik
                self.cik_to_name[cik] = name
                self.ticker_to_name[ticker.upper()] = name
                
                if cik not in self.exchange_data:
                    self.exchange_data[cik] = {}
                self.exchange_data[cik]['exchange'] = exchange
        
        print(f"Loaded {len(data_rows)} exchange ticker records")
    
    def load_all_data(self):
        """Load all SEC reference data."""
        print("Loading SEC reference data...")
        self.load_company_tickers()
        self.load_exchange_tickers()
        print("SEC reference data loaded successfully")
    
    def get_ticker_by_cik(self, cik: str) -> Optional[str]:
        """
        Get ticker symbol by CIK number.
        
        Args:
            cik: SEC CIK number (can be any length, will be padded)
            
        Returns:
            Ticker symbol or None if not found
        """
        cik_padded = str(cik).zfill(10)
        return self.cik_to_ticker.get(cik_padded)
    
    def get_cik_by_ticker(self, ticker: str) -> Optional[str]:
        """
        Get CIK number by ticker symbol.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            CIK number (10-digit string) or None if not found
        """
        return self.ticker_to_cik.get(ticker.upper())
    
    def get_company_name(self, identifier: str, is_cik: bool = False) -> Optional[str]:
        """
        Get company name by CIK or ticker.
        
        Args:
            identifier: CIK number or ticker symbol
            is_cik: True if identifier is CIK, False if ticker
            
        Returns:
            Company name or None if not found
        """
        if is_cik:
            cik = str(identifier).zfill(10)
            return self.cik_to_name.get(cik)
        else:
            ticker = identifier.upper()
            return self.ticker_to_name.get(ticker)
    
    def get_company_info(self, identifier: str) -> Optional[Dict]:
        """
        Get complete company information by ticker or CIK.
        
        Args:
            identifier: Ticker symbol or CIK number
            
        Returns:
            Dictionary with company info or None if not found
        """
        # Try as ticker first
        ticker = identifier.upper()
        cik = self.ticker_to_cik.get(ticker)
        
        # If not found, try as CIK
        if not cik:
            cik = str(identifier).zfill(10)
            ticker = self.cik_to_ticker.get(cik)
        
        if not cik or not ticker:
            return None
        
        return {
            'cik': cik,
            'ticker': ticker,
            'company_name': self.cik_to_name.get(cik, 'Unknown'),
            'exchange': self.exchange_data.get(cik, {}).get('exchange', 'Unknown')
        }
    
    def search_companies(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for companies by name or ticker.
        
        Args:
            query: Search string
            limit: Maximum number of results
            
        Returns:
            List of matching company info dictionaries
        """
        query_lower = query.lower()
        results = []
        
        # Search by ticker
        if query.upper() in self.ticker_to_cik:
            cik = self.ticker_to_cik[query.upper()]
            results.append({
                'cik': cik,
                'ticker': query.upper(),
                'company_name': self.cik_to_name.get(cik, 'Unknown'),
                'match_type': 'ticker_exact'
            })
        
        # Search by company name
        for cik, name in self.cik_to_name.items():
            if query_lower in name.lower():
                ticker = self.cik_to_ticker.get(cik, 'Unknown')
                results.append({
                    'cik': cik,
                    'ticker': ticker,
                    'company_name': name,
                    'match_type': 'name_partial'
                })
                if len(results) >= limit:
                    break
        
        return results[:limit]
    
    def get_all_tickers(self) -> List[str]:
        """Get list of all tickers in the database."""
        return list(self.ticker_to_cik.keys())
    
    def get_all_ciks(self) -> List[str]:
        """Get list of all CIKs in the database."""
        return list(self.cik_to_ticker.keys())
    
    def get_statistics(self) -> Dict:
        """Get statistics about the loaded data."""
        return {
            'total_companies': len(self.cik_to_ticker),
            'total_tickers': len(self.ticker_to_cik),
            'companies_with_exchange': len(self.exchange_data),
            'last_updated': datetime.now().isoformat()
        }
    
    def refresh_cache(self):
        """Force refresh of cached data."""
        print("Refreshing cache...")
        self.load_company_tickers()
        self.load_exchange_tickers()
        print("Cache refreshed successfully")
    
    def export_to_json(self, output_file: str = "sec_reference_data.json"):
        """
        Export all reference data to a JSON file.
        
        Args:
            output_file: Output filename
        """
        export_data = {
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'source': 'SEC EDGAR',
                'total_companies': len(self.cik_to_ticker)
            },
            'companies': []
        }
        
        for cik, ticker in self.cik_to_ticker.items():
            export_data['companies'].append({
                'cik': cik,
                'ticker': ticker,
                'company_name': self.cik_to_name.get(cik, 'Unknown'),
                'exchange': self.exchange_data.get(cik, {}).get('exchange', 'Unknown')
            })
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Exported {len(export_data['companies'])} companies to {output_file}")


# Simple sector classifier (no ML)
class SimpleSectorClassifier:
    """
    Simple sector classifier using keyword matching.
    No machine learning - just keyword lookup.
    """
    
    def __init__(self):
        self.sector_keywords = {
            'Technology': [
                'software', 'semiconductor', 'cloud', 'data', 'ai', 'artificial intelligence',
                'tech', 'digital', 'platform', 'internet', 'saas', 'computing', 'hardware',
                'electronics', 'chip', 'processor', 'analytics', 'cybersecurity'
            ],
            'Industrials': [
                'manufacturing', 'industrial', 'machinery', 'aerospace', 'defense',
                'logistics', 'transportation', 'engineering', 'automotive', 'construction',
                'equipment', 'aviation', 'rail', 'trucking', 'shipping'
            ],
            'Healthcare': [
                'biotech', 'pharmaceutical', 'pharma', 'medical', 'health', 'device',
                'diagnostic', 'hospital', 'therapeutic', 'clinical', 'laboratory',
                'genomics', 'biologics', 'healthcare', 'drug', 'medicine'
            ],
            'Financials': [
                'bank', 'banking', 'insurance', 'asset', 'capital', 'investment',
                'fintech', 'lending', 'wealth', 'brokerage', 'mortgage', 'credit',
                'financial', 'holdings', 'trust', 'advisory'
            ],
            'Consumer': [
                'retail', 'consumer', 'brand', 'restaurant', 'ecommerce', 'apparel',
                'grocery', 'hospitality', 'beverage', 'food', 'beauty', 'cosmetic',
                'fashion', 'clothing', 'household', 'product'
            ],
            'Energy': [
                'oil', 'gas', 'solar', 'renewable', 'energy', 'utility', 'wind',
                'drilling', 'pipeline', 'electric', 'power', 'petroleum', 'natural gas',
                'clean energy', 'battery', 'storage'
            ],
            'Real Estate': [
                'reit', 'real estate', 'property', 'trust', 'land', 'development',
                'residential', 'commercial', 'office', 'industrial reit'
            ],
            'Communication': [
                'telecom', 'telecommunications', 'media', 'broadcasting', 'cable',
                'wireless', 'network', 'satellite', 'entertainment', 'streaming'
            ]
        }
    
    def classify(self, company_name: str, description: str = "") -> str:
        """
        Classify a company's sector based on its name and description.
        
        Args:
            company_name: Company name
            description: Optional company description
            
        Returns:
            Sector name or 'Unknown'
        """
        text = (company_name + " " + description).lower()
        
        sector_scores = {}
        for sector, keywords in self.sector_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            if score > 0:
                sector_scores[sector] = score
        
        if not sector_scores:
            return 'Unknown'
        
        # Return sector with highest score
        return max(sector_scores, key=sector_scores.get)
    
    def get_all_sectors(self) -> List[str]:
        """Get list of all sectors."""
        return list(self.sector_keywords.keys())


# Example usage
if __name__ == "__main__":
    print("=" * 50)
    print("SEC Reference Data Manager")
    print("=" * 50)
    
    # Initialize the manager
    manager = SECReferenceDataManager()
    
    # Get statistics
    print("\n=== Statistics ===")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Look up by CIK
    print("\n=== Lookup by CIK ===")
    ticker = manager.get_ticker_by_cik("0001326801")
    print(f"CIK 0001326801 -> Ticker: {ticker}")
    
    # Look up by ticker
    print("\n=== Lookup by Ticker ===")
    cik = manager.get_cik_by_ticker("PLTR")
    print(f"Ticker PLTR -> CIK: {cik}")
    
    # Get company info
    print("\n=== Company Info ===")
    info = manager.get_company_info("PLTR")
    print(json.dumps(info, indent=2))
    
    # Search companies
    print("\n=== Search Results for 'apple' ===")
    results = manager.search_companies("apple", limit=3)
    for result in results:
        print(f"  {result['ticker']}: {result['company_name']}")
    
    # Test sector classifier
    print("\n=== Sector Classification ===")
    classifier = SimpleSectorClassifier()
    
    test_companies = [
        ("NVIDIA", "designs graphics processors and AI chips"),
        ("JPMorgan Chase", "banking and financial services"),
        ("Moderna", "biotechnology company developing mRNA medicines"),
        ("Home Depot", "home improvement retail")
    ]
    
    for name, desc in test_companies:
        sector = classifier.classify(name, desc)
        print(f"{name}: {sector}")
    
    print("\n=== Export to JSON ===")
    manager.export_to_json("sec_reference_data.json")
    print("Data exported successfully")
