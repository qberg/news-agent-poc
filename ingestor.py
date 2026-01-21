import pandas as pd
import feedparser
import trafilatura
import sqlite3
import hashlib
from loguru import logger


class NewsIngestor:
    def __init__(self, db_path="news_data.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                source_name TEXT,
                url TEXT,
                title TEXT,
                content TEXT,
                published_date TEXT
            )
            """)
        self.conn.commit()

    def get_url_hash(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def is_new(self, url_hash):
        cursor = self.conn.execute("SELECT 1 FROM articles WHERE id = ?", (url_hash,))
        return cursor.fetchone() is None

    def process_raw_sources(self, csv_path):
        df = pd.read_csv(csv_path)
        rss_sources = df[df["Final_Tier"] == "TIER_1_RSS"].to_dict("records")

        for source in rss_sources:
            logger.info(f"Fetching: {source['Source Name']}")
            feed = feedparser.parse(source["Verified_RSS"])

            for entry in feed.entries:
                url = entry.link
                url_hash = self.get_url_hash(url)

                if self.is_new(url_hash):
                    logger.info(f"Extracting: {url}")
                    downloaded = trafilatura.fetch_url(url)
                    content = trafilatura.extract(downloaded)

                    if content:
                        self.conn.execute(
                            "INSERT INTO articles VALUES (?, ?, ?, ?, ?, ?)",
                            (
                                url_hash,
                                source["Source Name"],
                                url,
                                entry.title,
                                content,
                                getattr(entry, "published", ""),
                            ),
                        )
                        self.conn.commit()
                    else:
                        logger.warning(f"Failed to extract content from {url}")

                else:
                    logger.debug(f"Duplicate found, skipping: {url}")


if __name__ == "__main__":
    ingestor = NewsIngestor()
    ingestor.process_raw_sources("./audit_results.csv")
    logger.success("Ingestion complete. Database 'news_data.db' is ready.")
