#!/usr/bin/env python3
import json
import pathlib
import pandas as pd
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta  # pip install python-dateutil

def extract_search_query(title):
    """Extract the actual search query from the title."""
    if not title:
        return ''
    
    # Russian format: 'Выполнен поиск по запросу [query]' or similar
    if title.startswith('Выполнен поиск'):
        return title.replace('Выполнен поиск', '').replace('по запросу', '').strip(' :"\'')
    # English format: 'Searched for [query]' or similar
    elif title.startswith('Searched for'):
        return title.replace('Searched for', '').strip(' :"\'')
    return ''

def main():
    print("Starting Google Takeout Search Stats script...")
    
    # Set up file paths
    takeout_dir = pathlib.Path('data') / 'Takeout'
    activity_file = takeout_dir / 'Мои действия' / 'Поиск' / 'МоиДействия.json'
    
    print(f"Looking for data file at: {activity_file}")
    print(f"File exists: {activity_file.exists()}")
    
    if not activity_file.exists():
        print("Error: Data file not found. Please ensure the file exists at the specified path.")
        return
    
    try:
        # Load and parse the JSON data
        print("\nLoading JSON data...")
        with activity_file.open(encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"Loaded {len(data) if isinstance(data, list) else 'unknown number of'} items from JSON")
        
        # Print first few items for debugging
        print("\nFirst 3 items in data:")
        for i, item in enumerate(data[:3]):
            print(f"Item {i+1}: {item.get('title', 'No title')} - {item.get('time', 'No time')}")
        
        # Process search records
        records = []
        search_phrases = ('Выполнен поиск', 'Searched for')
        
        for item in data:
            title = item.get('title', '')
            if title.startswith(search_phrases):
                try:
                    # Parse timestamp
                    ts = datetime.fromisoformat(item['time'].replace('Z', '+00:00'))
                    
                    # Extract search query
                    query = extract_search_query(title)
                    
                    records.append({
                        'datetime': ts,
                        'query': query,
                        'title': title  # Keep original title for reference
                    })
                except Exception as e:
                    print(f"Warning: Could not process item: {e}")
                    continue
        
        print(f"\nFound {len(records)} search records")
        
        if not records:
            print("\nNo search records found. The script is looking for titles starting with:")
            print("  - 'Выполнен поиск' (Russian)")
            print("  - 'Searched for' (English)")
            return
        
        # Create a DataFrame with all search queries
        all_queries_df = pd.DataFrame(records)
        
        # Save all queries to CSV
        all_queries_file = 'data/all_search_queries.csv'
        all_queries_df[['datetime', 'query']].to_csv(all_queries_file, index=False, encoding='utf-8-sig')
        print(f"\nSaved {len(all_queries_df)} search queries to {all_queries_file}")
        
        # Show sample of the data
        print("\nSample of search queries:")
        print(all_queries_df[['datetime', 'query']].head().to_string(index=False))
        
        # Generate monthly statistics for all time
        print("\nGenerating monthly statistics for all available data...")
        
        # Use all records for monthly statistics
        monthly = (
            all_queries_df.set_index('datetime')
            .groupby(pd.Grouper(freq='M'))
            .size()
            .rename('queries')
            .to_frame()
            .sort_index()
        )
        
        # Calculate and display date range
        min_date = all_queries_df['datetime'].min()
        max_date = all_queries_df['datetime'].max()
        print(f"Data covers period from {min_date} to {max_date}")
            
        # Save monthly stats to CSV
        monthly_file = 'data/search_queries_by_month.csv'
        monthly.to_csv(monthly_file, encoding='utf-8-sig')
        
        # Calculate and display total queries
        total_queries = monthly['queries'].sum()
        print(f"\nFound {total_queries:,} total search queries across {len(monthly)} months")
        
        print("\nMonthly search queries summary:")
        print(monthly.to_string())
        print(f"\nMonthly statistics saved to {monthly_file}")
        
        # Save full data with year and month columns for better filtering
        all_queries_df['year'] = all_queries_df['datetime'].dt.year
        all_queries_df['month'] = all_queries_df['datetime'].dt.month
        all_queries_df['date'] = all_queries_df['datetime'].dt.date
        all_queries_df[['date', 'year', 'month', 'query', 'title']].to_csv('data/all_search_queries_detailed.csv', index=False, encoding='utf-8-sig')
        print("\nDetailed search queries with date information saved to 'all_search_queries_detailed.csv'")
        
        print("\nScript completed successfully!")
        
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON data: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
