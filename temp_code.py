Here's a Python script that uses BeautifulSoup to extract the specified review details from the provided HTML content. The extracted reviews are formatted as JSON.

```python
from bs4 import BeautifulSoup
import json

# Sample HTML content (replace this with the actual HTML content)
html_content = """
<!-- Your provided HTML content goes here -->
"""

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Initialize a list to hold the extracted reviews
reviews = []

# Find all review blocks
review_blocks = soup.find_all('span', class_='a-profile-name')

for review_block in review_blocks:
    # Extract reviewer's ID
    reviewer_id = review_block.find_previous('span').text.strip()
    
    # Extract reviewer's name
    reviewer_name = review_block.text.strip()
    
    # Extract reviewer's link
    reviewer_link = review_block.find_parent('a')['href']
    
    # Extract rating
    rating_block = review_block.find_next('span', class_='a-icon-alt')
    rating = rating_block.text.split()[0] if rating_block else None
    
    # Extract review title
    review_title_block = review_block.find_next('a', class_='a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold')
    review_title = review_title_block.text.strip() if review_title_block else None
    
    # Extract review date
    review_date_block = review_title_block.find_next('span', class_='a-size-base a-color-secondary review-date')
    review_date = review_date_block.text.strip() if review_date_block else None
    
    # Extract review description
    review_description_block = review_date_block.find_next('span', class_='a-size-base review-text review-text-content')
    review_description = review_description_block.text.strip() if review_description_block else None
    
    # Check if the review is from the United States
    if "Reviewed in the United States" in review_date:
        # Create a review dictionary
        review = {
            "reviewer_id": reviewer_id,
            "reviewer_name": reviewer_name,
            "reviewer_link": reviewer_link,
            "rating": rating,
            "review_title": review_title,
            "review_date": review_date,
            "review_description": review_description
        }
        reviews.append(review)

# Convert the list of reviews to JSON
reviews_json = json.dumps(reviews, indent=4)

# Print the JSON output
print(reviews_json)
```

### Explanation:
1. **HTML Parsing**: The script uses BeautifulSoup to parse the provided HTML content.
2. **Review Extraction**: It iterates through each review block, extracting the required details:
   - Reviewer's ID
   - Reviewer's name
   - Reviewer's link
   - Rating
   - Review title
   - Review date
   - Review description
3. **US Reviews Filtering**: It checks if the review is from the United States by looking for "Reviewed in the United States" in the review date.
4. **JSON Formatting**: The extracted reviews are formatted as JSON and printed.

### Note:
- Replace the `html_content` variable with the actual HTML content you want to parse.
- Ensure that the HTML structure remains consistent with the provided example for the script to work correctly.