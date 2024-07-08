import io

import pandas as pd
import requests
from celery import shared_task
from django.db import transaction

from api.models import Game


@shared_task
def process_csv_file(url):
    try:
        # Stream the file to handle large sizes
        with requests.get(url, stream=True) as r:
            r.raise_for_status()

            # Check file size
            content_length = int(r.headers.get("Content-Length", 0))
            if content_length > 157286400:  # 150 MB in bytes
                return {"error": "File too large, maximum size is 150 MB"}

            # Read the CSV content in chunks
            chunks = []
            for chunk in r.iter_content(chunk_size=8192):
                chunks.append(chunk)

            csv_content = b"".join(chunks).decode("utf-8")
            df = pd.read_csv(io.StringIO(csv_content))

            # Ensure data types match the sample CSV
            df["Release date"] = pd.to_datetime(df["Release date"], format="mixed")
            df["Required age"] = df["Required age"].astype(int)
            df["Price"] = df["Price"].astype(float)
            df["DLC count"] = df["DLC count"].astype(int)
            df["Positive"] = df["Positive"].astype(int)
            df["Negative"] = df["Negative"].astype(int)

            # Save or update data in the database
            with transaction.atomic():
                game_instances = []
                for _, row in df.iterrows():

                    game_instances.append(
                        Game(
                            app_id=row["AppID"],
                            name=row["Name"],
                            release_date=row["Release date"],
                            required_age=row["Required age"],
                            price=row["Price"],
                            dlc_count=row["DLC count"],
                            about=row["About the game"],
                            supported_languages=row["Supported languages"],
                            windows=row["Windows"],
                            mac=row["Mac"],
                            linux=row["Linux"],
                            positive=row["Positive"],
                            negative=row["Negative"],
                            score_rank=row["Score rank"],
                            developers=row["Developers"],
                            publishers=row["Publishers"],
                            categories=row["Categories"],
                            genres=row["Genres"],
                            tags=row["Tags"],
                        )
                    )
                    Game.objects.bulk_create(
                        game_instances,
                        batch_size=10000,
                        update_conflicts=True,
                        update_fields=[
                            "name",
                            "release_date",
                            "required_age",
                            "price",
                            "dlc_count",
                            "about",
                            "supported_languages",
                            "windows",
                            "mac",
                            "linux",
                            "positive",
                            "negative",
                            "score_rank",
                            "developers",
                            "publishers",
                            "categories",
                            "genres",
                            "tags",
                        ],
                        unique_fields=["app_id"],
                    )

        return {"message": "CSV file processed successfully"}
    except Exception as e:
        return {"error": str(e)}
