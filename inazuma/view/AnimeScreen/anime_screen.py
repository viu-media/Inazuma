import logging

from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.widget import Factory
from kivymd.uix.button import MDButton

from ...view.base_screen import BaseScreenView
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from viu_media.libs.media_api.types import MediaItem
    from viu_media.libs.provider.anime.types import Server, Anime
    from inazuma.controller.anime_screen import AnimeScreenController
logger = logging.getLogger((__name__))


class EpisodeButton(MDButton):
    text = StringProperty()
    change_episode_callback = ObjectProperty()


Factory.register("EpisodeButton", cls=EpisodeButton)


class AnimeScreenView(BaseScreenView):
    """The anime screen view"""

    controller: "AnimeScreenController"
    current_media_item: "MediaItem | None" = None
    current_server = ObjectProperty()
    current_link = StringProperty()
    current_servers: "list[Server]" = ListProperty([])
    current_anime_data = ObjectProperty()
    caller_screen_name = ObjectProperty()
    current_title = ""
    episodes_container = ObjectProperty()
    episodes_list = []
    current_episode_index = 0
    current_episode = 1
    video_player = ObjectProperty()
    anime_title_label = ObjectProperty()
    current_server_name = "sharepoint"
    is_dub = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.update_episodes(100)

    def update_episodes(self, episodes_list):
        self.episodes_container.data = []
        self.episodes_list = episodes_list
        for episode in episodes_list:
            self.episodes_container.data.append(
                {
                    "viewclass": "EpisodeButton",
                    "text": str(episode),
                    "change_episode_callback": lambda x=episode: self.update_current_episode(
                        x
                    ),
                }
            )

    def next_episode(self):
        next_index = self.current_episode_index + 1
        if next_index < len(self.episodes_list):
            next_episode = self.episodes_list[next_index]
            self.update_current_episode(next_episode)

    def previous_episode(self):
        previous_index = self.current_episode_index - 1
        if previous_index >= 0:
            previous_episode = self.episodes_list[previous_index]
            self.update_current_episode(previous_episode)

    def on_current_anime_data(self, instance, anime: "Anime"):
        self.anime_title_label.text = self.current_media_item.title.english if self.current_media_item else "Loading..."
        episodes = anime.episodes.sub if True else anime.episodes.dub
        self.update_episodes(episodes)
        if self.episodes_list:
            self.current_episode_index = 0
            self.current_episode = self.episodes_list[0]
        self.update_current_video_stream(self.current_server_name)
        self.video_player.state = "play"

    def update_current_episode(self, episode):
        self.current_episode = episode
        if episode in self.episodes_list:
            self.current_episode_index = self.episodes_list.index(episode)
        self.controller.fetch_streams(episode)
        self.update_current_video_stream(self.current_server_name)
        self.video_player.state = "play"

    def update_current_video_stream(self, server_name: str):
        for server in self.current_servers:
            if server.name == server_name:
                self.current_server = server
                self.current_server_name = server.name
                self.current_link = server.links[0].link
                self.video_player.state = "play"
                logger.debug(f"found {self.current_server_name} server")
                logger.debug(f"found {self.current_link} link")
                break
            else:
                logger.warning(f"Found {server.name} server but {server_name} wanted")

    def add_to_user_anime_list(self, *args):
        self.app.add_anime_to_user_anime_list(self.model.anime_id)


__all__ = ["AnimeScreenView"]
