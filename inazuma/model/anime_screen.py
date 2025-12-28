# from viu_media.libs.media_api.api import create_api_client
# from viu_media.libs.provider.anime.provider import create_provider

# from viu_media.libs.media_api.types import MediaSearchResult
# from viu_media.cli.utils.search import find_best_match_title
# from viu_media.libs.provider.anime.types import ProviderName
from kivy.cache import Cache
from kivy.logger import Logger

from .base_model import BaseScreenModel
from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from viu_media.libs.media_api.types import MediaItem
    from viu_media.libs.provider.anime.types import Anime, Server, EpisodeStream
    from inazuma.core.viu import Viu
Cache.register("streams.anime", limit=10)

# anime_provider = create_provider(ProviderName.ALLANIME)


@dataclass
class CurrentState:
    media_item: "MediaItem | None" = None
    provider_anime: "Anime | None" = None
    episode_stream: "EpisodeStream | None" = None


class AnimeScreenModel(BaseScreenModel):
    """the Anime screen model"""

    # data = {}
    # anime_id = 0
    # current_anime_data = None
    # current_anilist_anime_id = "0"
    # current_provider_anime_id = "0"
    # current_title = ""
    # media_search_result: "MediaSearchResult | None" = None
    viu: "Viu"

    def __init__(self, viu: "Viu") -> None:
        super().__init__()
        self.viu = viu
        self.current_state = CurrentState()

    def get_anime_data_from_provider(self, media_item: "MediaItem") -> "Anime | None":
        from viu_media.libs.provider.anime.params import SearchParams, AnimeParams
        from viu_media.cli.utils.search import find_best_match_title

        try:
            anime_provider = self.viu.anime_provider
            # if (self.media_search_result or {"id": -1})["id"] == media_search_result[
            #     "id"
            # ] and self.current_anime_data:
            #     return self.current_anime_data

            search_results = anime_provider.search(
                SearchParams(
                    query=media_item.title.romaji or media_item.title.english,
                    translation_type=self.viu.config.stream.translation_type,
                )
            )

            if not search_results:
                return
            provider_results_map = {
                result.title: result for result in search_results.results
            }
            result = find_best_match_title(
                provider_results_map,
                self.viu.config.general.provider,
                media_item,
            )
            provider_anime = provider_results_map[result]
            initial_state = self.current_state
            self.current_state.provider_anime = (
                anime_provider.get(
                    AnimeParams(
                        query=media_item.title.romaji or media_item.title.english,
                        id=provider_anime.id,
                    )
                )
                or initial_state.provider_anime
            )

            if (
                initial_state.provider_anime != self.current_state.provider_anime
                and self.current_state.provider_anime
            ):
                Logger.debug(
                    f"Got data of {provider_anime.title} from {self.viu.config.general.provider} provider"
                )

            self.current_state.media_item = media_item
            return self.current_state.provider_anime
        except Exception as e:
            Logger.info("anime_screen error: %s" % e)
            return

    def get_episode_streams(self, episode: str) -> list["Server"]:
        from viu_media.libs.provider.anime.params import EpisodeStreamsParams

        try:
            if not (
                self.current_state.provider_anime and self.current_state.media_item
            ):
                return []

            streams = self.viu.anime_provider.episode_streams(
                EpisodeStreamsParams(
                    query=self.current_state.media_item.title.romaji
                    or self.current_state.media_item.title.english,
                    anime_id=self.current_state.provider_anime.id,
                    episode=episode,
                    translation_type=self.viu.config.stream.translation_type,
                )
            )

            if not streams:
                return []

            return [episode_stream for episode_stream in streams]

        except Exception as e:
            Logger.error("anime_screen error: %s" % e)
            return []

    # def get_anime_data(self, id: int):
    #     return AniList.get_anime(id)


__all__ = ["AnimeScreenModel"]
