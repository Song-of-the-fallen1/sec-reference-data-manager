# SEC Reference Data Manager

Manages SEC reference data including CIK to ticker mappings, company metadata, and sector classification. Downloads and parses SEC's public JSON files - no API key required.

## Features

- CIK to Ticker Resolution: Convert SEC CIK numbers to stock tickers
- Ticker to CIK Resolution: Convert stock tickers to SEC CIK numbers
- Company Name Lookup: Get company names by CIK or ticker
- Company Search: Search for companies by name or ticker
- Exchange Data: Track which exchange each company trades on
- Local Caching: 24-hour cache to reduce SEC server load
- Sector Classification: Simple keyword-based sector classification (no ML)
- JSON Export: Export all reference data to JSON for offline use

## Data Sources

| Source | URL | Description |
|--------|-----|-------------|
| Company Tickers | https://www.sec.gov/files/company_tickers.json | Basic CIK to ticker mapping |
| Exchange Tickers | https://www.sec.gov/files/company_tickers_exchange.json | Extended data with exchange info |

## Installation

```bash
# No external dependencies - uses only Python standard library
