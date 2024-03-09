# Ghost ASIN Scraper

1. Upload CSV in the side panel.

*Note the CSV you upload should have these columns.*

| UPC/EAN | product | cost | 
| -------- | ------- | ------- | 
| 12345 | Jordan 1 Off White Chicago | 180 |
| 34567 | Nike Dunk Low Pandas | 120 | 

2. Wait for image scraper to complete
   - Searches Amazon by UPC/EAN
   - Uses LLM (OpenAI) to find matches
   - Cleans up search term and researches Amazon
   - Uses LLM (OpenAI) to find matches again

3. Download CSV