from typing import TYPE_CHECKING

from viu_media.libs.media_api.params import MediaSearchParams
from viu_media.libs.media_api.types import (
    MediaFormat,
    MediaGenre,
    MediaSeason,
    MediaSort,
)

from .base_model import BaseScreenModel

if TYPE_CHECKING:
    from inazuma.core.viu import Viu


class SearchScreenModel(BaseScreenModel):
    viu: "Viu"

    def __init__(self, viu: "Viu") -> None:
        super().__init__()
        self.viu = viu

    def get_trending(self):
        return self.viu.media_api.search_media(
            MediaSearchParams(
                sort=MediaSort.TRENDING_DESC, per_page=self.viu.config.anilist.per_page
            )
        )

    def search_for_anime(self, anime_title, filters={}):
        # Filter out disabled/None values
        filters = {k: v for k, v in filters.items() if v not in [None, "DISABLED"]}

        # Build search params with proper type conversions
        search_params = {}

        # Only add query if there's a search term
        if anime_title and anime_title.strip():
            search_params["query"] = anime_title

        # Handle page
        if "page" in filters:
            search_params["page"] = filters["page"]

        # Handle sort
        if "sort" in filters:
            search_params["sort"] = MediaSort[filters["sort"]]

        # Handle status
        if "status" in filters:
            from viu_media.libs.media_api.types import MediaStatus

            search_params["status"] = MediaStatus[filters["status"]]

        # Handle genre (as list for genre_in)
        if "genre" in filters:
            search_params["genre_in"] = [MediaGenre[filters["genre"]]]

        # Handle format (as list for format_in)
        if "format" in filters:
            search_params["format_in"] = [MediaFormat[filters["format"]]]

        # Handle season
        if "season" in filters:
            search_params["season"] = MediaSeason[filters["season"]]

        # Handle year (seasonYear)
        if "year" in filters:
            search_params["seasonYear"] = int(filters["year"])

        return self.viu.media_api.search_media(MediaSearchParams(**search_params))


__all__ = ["SearchScreenModel"]
