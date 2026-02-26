import scrapy
from ..items import UserReviewItem

class MetacriticUserReviewSpider(scrapy.Spider):
    name = "metacritic_userreview"
    allowed_domains = ["metacritic.com"]
    # Define Starting URL
    start_urls = ["https://www.metacritic.com/browse/movie/"]

    def __init__(self, limit=10, *args, **kwargs):
        super(MetacriticUserReviewSpider, self).__init__(*args, **kwargs)
        self.limit = int(limit)

    def parse(self, response):
        current_page = response.meta.get("current_page", 1)
        processed_count = response.meta.get("processed_count", 0)
        # This selector defines every movie on the page (movie cards)
        movie_cards = response.css("div.c-finderProductCard")

        for card in movie_cards:
            if processed_count >= self.limit:
                return
            
            # Extract general data before moving deeper
            title = card.css(".c-finderProductCard_titleHeading span:nth-child(2)::text").get()

            # Get the relative URL
            relative_url = card.css('a.c-finderProductCard_container::attr(href)').get()

            if relative_url:
                processed_count += 1
                movie_info = {
                "movie_title" : title.strip() if title else "Unknown Title"
        }         

                # Follow the movie link into the page to get the full critic review data
                yield scrapy.Request(
                    url= response.urljoin(relative_url) + "user-reviews/",
                    callback=self.parse_user_reviews,
                    meta={"movie_info": movie_info, "playwright":True, "playwright_include_page": True, "playwright_context": "brightdata", "playwright_page_manage": False}
                    )
                
        # URL-based pagination
        if processed_count < self.limit:
            next_page_num = current_page + 1
            #Rebuild the next page url
            next_page_url = f"https://www.metacritic.com/browse/movie/?releaseYearMin=1910&releaseYearMax=2026&page={next_page_num}"

            self.logger.info(f"Moving onto page {next_page_num}")

            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                meta={
                    "current_page": next_page_num,
                    "processed_count": processed_count
                }
            )
        
    async def parse_user_reviews(self, response):
        page = response.meta["playwright_page"]
        movie_info = response.meta["movie_info"]

        try:
            # Wait for the main reviews container seen in the inspector
            await page.wait_for_selector('div[data-testid="product-reviews"]', timeout=15000)

            # 1. Capture the Average User Score for the movie
            avg_score_el = await page.query_selector('div[data-testid="score-card-overview"] .c-siteReviewScore_background-user span')
            avg_userscore = await avg_score_el.inner_text() if avg_score_el else "0"

            # 2. Scrolling loop to trigger lazy loading
            for _ in range(5):
                await page.mouse.wheel(0, 1500)
                await page.wait_for_timeout(800)

            # 3. Use verified selectors inside the JS evaluator
            reviews_data = await page.evaluate("""
                () => {
                    const container = document.querySelector('div[data-testid="product-reviews"]');
                    if (!container) return [];
                    
                    const items = container.querySelectorAll('.c-siteReview');
                    return Array.from(items).map(item => ({
                        username: item.querySelector('.c-siteReviewHeader_username')?.innerText || 'N/A',
                        individualScore: item.querySelector('.c-siteReviewScore span')?.innerText || '0',
                        date: item.querySelector('.c-siteReview_reviewDate')?.innerText || 'N/A',
                        text: item.querySelector('.c-siteReview_quote span')?.innerText || 'N/A'
                    }));
                }
            """)

            self.logger.info(f"Successfully captured {len(reviews_data)} user reviews for {movie_info['movie_title']}")

            # 4. Map browser data to Scrapy UserReviewItem fields
            for data in reviews_data:
                item = UserReviewItem()
                item["movie_title"] = movie_info["movie_title"]
                item["average_userscore"] = avg_userscore.strip()
                item["username"] = data["username"].strip()
                item["individual_userscore"] = data["individualScore"].strip()
                item["review_date"] = data["date"].strip()
                item["user_review"] = data["text"].strip()
                yield item

        except Exception as e:
            self.logger.error(f"Logic failure on {movie_info['movie_title']}: {e}")
        finally:
            # Close the page to manage memory
            await page.close()