import logging

from kivy.properties import ListProperty, ObjectProperty, StringProperty
from kivy.uix.widget import Factory
from kivymd.uix.button import MDButton
from kivymd.uix.menu import MDDropdownMenu


from ...view.base_screen import BaseScreenView
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from viu_media.libs.media_api.types import MediaItem
    from viu_media.libs.provider.anime.types import ProviderName

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
    servers_container = ObjectProperty()
    episodes_list = []
    current_episode_index = 0
    current_episode = 1
    video_player = ObjectProperty()
    anime_title_label = ObjectProperty()
    current_server_name = StringProperty("sharepoint")
    current_translation_type = StringProperty("sub")
    current_provider = StringProperty("allanime")

    _translation_menu: MDDropdownMenu | None = None
    _provider_menu: MDDropdownMenu | None = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.update_episodes(100)
        self.current_provider = self.app.viu.config.general.provider.value
        self.current_translation_type = self.app.viu.config.stream.translation_type
        self.current_server_name = self.app.viu.config.stream.server.value

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
        self.anime_title_label.text = (
            self.current_media_item.title.english
            if self.current_media_item
            else "Loading..."
        )
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
            if server_name == "TOP":
                server_name = server.name
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

    def on_current_servers(self, instance, servers):
        """Called when current_servers changes - populate the segmented button."""
        from kivymd.uix.segmentedbutton import (
            MDSegmentedButton,
            MDSegmentedButtonItem,
            MDSegmentButtonLabel,
        )

        if not self.servers_container:
            return

        # Clear existing items
        self.servers_container.clear_widgets()

        if not servers:
            return

        # Create segmented button with server items
        segmented_btn = MDSegmentedButton(multiselect=False)

        for server in servers:
            item = MDSegmentedButtonItem()
            label = MDSegmentButtonLabel(text=server.name.title())
            item.add_widget(label)

            # Bind using active property observer
            def make_callback(srv):
                def callback(instance, active):
                    logger.info(f"Server button clicked: {srv.name}, active: {active}")
                    if active:
                        self.update_current_video_stream(srv.name)

                return callback

            item.bind(active=make_callback(server))
            segmented_btn.add_widget(item)

        self.servers_container.add_widget(segmented_btn)

        # Select first server by default if available
        if segmented_btn.children and servers:
            first_item = segmented_btn.children[-1]  # Children are reversed
            segmented_btn.selected_segments = [first_item]

    def open_translation_menu(self, button):
        """Open the translation type dropdown menu."""
        if not self._translation_menu:
            menu_items = [
                {
                    "text": "Sub",
                    "on_release": lambda: self._set_translation_type("sub"),
                },
                {
                    "text": "Dub",
                    "on_release": lambda: self._set_translation_type("dub"),
                },
            ]
            self._translation_menu = MDDropdownMenu(
                caller=button,
                items=menu_items,
            )
        if self._translation_menu:
            self._translation_menu.caller = button
            self._translation_menu.open()

    def _set_translation_type(self, translation_type: Literal["sub", "dub"]):
        """Set the translation type in viu config."""
        self.app.viu.config.stream.translation_type = translation_type
        self.current_translation_type = translation_type.title()
        if self._translation_menu:
            self._translation_menu.dismiss()
        logger.info(f"Translation type set to: {translation_type}")

    def open_provider_menu(self, button):
        """Open the provider dropdown menu."""
        from viu_media.libs.provider.anime.types import ProviderName

        if not self._provider_menu:
            menu_items = [
                {
                    "text": provider.value.title(),
                    "on_release": lambda p=provider: self._set_provider(p),
                }
                for provider in ProviderName
            ]
            self._provider_menu = MDDropdownMenu(
                caller=button,
                items=menu_items,
            )
        if self._provider_menu:
            self._provider_menu.caller = button
            self._provider_menu.open()

    def _set_provider(self, provider: "ProviderName"):
        """Set the provider in viu config and reset viu services."""

        self.app.viu.config.general.provider = provider
        self.current_provider = provider.value
        self.app.viu._anime_provider = None  # Reset the cached provider
        self.model.get_anime_data_from_provider(self.current_media_item)
        if self._provider_menu:
            self._provider_menu.dismiss()
        logger.info(f"Provider set to: {provider.value}, viu services reset")

    def add_to_user_anime_list(self, *args):
        self.app.add_anime_to_user_anime_list(self.model.anime_id)


__all__ = ["AnimeScreenView"]
