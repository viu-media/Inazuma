from typing import TYPE_CHECKING

from kivy.cache import Cache
from kivy.logger import Logger
from inazuma.model.anime_screen import AnimeScreenModel
from inazuma.view.AnimeScreen.anime_screen import AnimeScreenView

if TYPE_CHECKING:
    from viu_media.libs.media_api.types import MediaItem

Cache.register("data.anime", limit=20, timeout=600)


class AnimeScreenController:
    """The controller for the anime screen"""

    def __init__(self, model: AnimeScreenModel):
        self.model = model
        self.view = AnimeScreenView(controller=self, model=self.model)

    def get_view(self) -> AnimeScreenView:
        return self.view

    def fetch_streams(self, episode="1"):
        if not self.model.current_state.provider_anime:
            Logger.warning("No provider anime data available to fetch streams.")
            return

        if current_servers := self.model.get_episode_streams(episode):
            Logger.debug(
                f"current servers {[server.name for server in current_servers]}"
            )
            self.view.current_servers = current_servers
        else:
            Logger.warning(
                f"No servers found for {self.model.current_state.provider_anime.title}"
            )

        # TODO: add auto start
        #
        # self.view.current_link = self.view.current_links[0]["gogoanime"][0]

    def update_anime_view(self, media_item: "MediaItem", caller_screen_name):
        self.model.get_anime_data_from_provider(media_item)
        self.view.current_media_item = media_item
        self.view.current_anime_data = self.model.current_state.provider_anime
        self.view.current_title = media_item.title.romaji or media_item.title.english
        self.view.caller_screen_name = caller_screen_name


__all__ = ["AnimeScreenController"]
