import scrapy
from ..items import CriticReviewItem

class MetacriticCriticReviewSpider(scrapy.Spider):
    name = "metacritic_criticreview"
    allowed_domains = ["metacritic.com"]
    # Define Starting URL
    start_urls = ["https://www.metacritic.com/browse/movie/"]

    def __init__(self, limit=10, *args, **kwargs):
        super(MetacriticCriticReviewSpider, self).__init__(*args, **kwargs)
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
            score = card.css("div.c-siteReviewScore span::text").get()

            # Get the relative URL
            relative_url = card.css('a.c-finderProductCard_container::attr(href)').get()

            if relative_url:
                processed_count += 1
                movie_info = {
                "movie_title" : title.strip() if title else "Unknown Title",
                "average_metascore" : score.strip() if score else "0"
        }         

                # Follow the movie link into the page to get the full critic review data
                yield scrapy.Request(
                    url= response.urljoin(relative_url) + "critic-reviews/",
                    callback=self.parse_critic_reviews,
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
        
    async def parse_critic_reviews(self, response):
        page = response.meta["playwright_page"]
        movie_info = response.meta["movie_info"]

        try:
            # 1. Wait for the big wrapper
            await page.wait_for_selector('div[data-testid="product-reviews"]', timeout=15000)

            # 2. Scrolling: "Nudge" the page to make sure all  items load
            for _ in range(5):
                await page.mouse.wheel(0, 1000)
                await page.wait_for_timeout(600)

            # 3. Extraction: Use the structure of metadata to extract each movie on the page
            reviews_data = await page.evaluate("""
                () => {
                    const container = document.querySelector('div[data-testid="product-reviews"]');
                    if (!container) return [];
                    
                    const items = container.querySelectorAll('.c-siteReview');
                    return Array.from(items).map(item => ({
                        name: item.querySelector('.c-siteReview_criticName')?.innerText || 'N/A',
                        score: item.querySelector('.c-siteReviewScore span')?.innerText || '0',
                        pub: item.querySelector('.c-siteReviewHeader_publicationName')?.innerText || 'N/A',
                        text: item.querySelector('.c-siteReview_quote span')?.innerText || 'N/A'
                    }));
                }
            """)

            self.logger.info(f"Successfully captured {len(reviews_data)} reviews for {movie_info['movie_title']}")

            # 4. Turn the browser data into Scrapy items
            for data in reviews_data:
                item = CriticReviewItem()
                item["movie_title"] = movie_info["movie_title"]
                item["average_metascore"] = movie_info["average_metascore"]
                item["critic_name"] = data["name"].replace("By ", "").strip()
                item["critic_score"] = data["score"]
                item["publication"] = data["pub"].strip()
                item["critic_review"] = data["text"].strip()
                yield item

        except Exception as e:
            self.logger.error(f"Logic failure on {movie_info['movie_title']}: {e}")
        finally:
            # Crucial: Close the tab after yielding all items
            await page.close()