# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import re
from itemadapter import ItemAdapter


class CriticReviewsPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        # Safety check to ensure that metascore and critic score are numbers
        critic_numeric_items = ["average_metascore", "critic_score"]
        for numbers in critic_numeric_items:
            value = item.get(numbers)
            if value:
                try:
                    item[numbers] = int(value)
                # Fallback in case score isn't a valid number
                except (ValueError, TypeError):
                    item[numbers] = 0

        # Safety check to ensure text items don't have weird symbols or leading/trailing characters
        critic_text_items = ["critic_name", "publication"]
        for texts in critic_text_items:
            if item.get(texts):
                # Remove emojis and any other weird symbols 
                cleaned = re.sub(r'[^\w\s.,!?\'"\-]', '', item[texts])
                # Normalize whitespace
                item[texts] = " ".join(cleaned.split())

        return item