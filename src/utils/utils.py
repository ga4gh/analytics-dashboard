from datetime import datetime
from typing import Optional

def parse_date(date_str: str) -> Optional[datetime]:
      """
      Parse date string into datetime object.
      Handles various formats: "2024 Jan 15", "2024 Jan", "2024"
      """
      if not date_str:
          return None

      date_formats = [
          "%Y %b %d",     # "2024 Jan 15"
          "%Y %B %d",     # "2024 January 15"
          "%Y %b",        # "2024 Jan"
          "%Y %B",        # "2024 January"
          "%Y",           # "2024"
          "%Y-%m-%d",     # "2024-01-15" 
          "%Y/%m/%d",     # "2024/01/15"
      ]

      for fmt in date_formats:
          try:
              return datetime.strptime(date_str, fmt)
          except ValueError:
              continue

      # If no format matches, try to extract just the year
      try:
          year_match = date_str.split()[0]
          if year_match.isdigit() and len(year_match) == 4:
              return datetime(int(year_match), 1, 1)  # Default to Jan 1
      except (IndexError, ValueError):
          pass

      print(f"Warning: Could not parse date '{date_str}'")
      return None