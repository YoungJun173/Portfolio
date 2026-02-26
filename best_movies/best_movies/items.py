# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.item import Item, Field

class BaseReviewItem(scrapy.Item):
    movie_title = scrapy.Field()            # Name of movie
    pass

class CriticReviewItem(BaseReviewItem):
    average_metascore = scrapy.Field()      # Metascore (Average Metascore Based on Critic Metascores)
    critic_review = scrapy.Field()          # Critic Review
    critic_name = scrapy.Field()            # Critic Name
    critic_score = scrapy.Field()           # Critic Score
    publication = scrapy.Field()            # Critic Publication
    pass

class UserReviewItem(BaseReviewItem):
    average_userscore = scrapy.Field()      # Userscore (Average Userscore Based on Individual Userscores)
    user_review = scrapy.Field()            # User Review
    username = scrapy.Field()               # Username
    review_date = scrapy.Field()            # Date of Review
    individual_userscore = scrapy.Field()   # Individual Userscore per Reviewer
    pass