import json
import os
import random

from kivy.resources import resource_find
from kivy.uix.screenmanager import FadeTransition, ScreenManager
from kivy.uix.settings import SettingsWithSidebar
from kivymd.app import MDApp
from inazuma.view.screens import screens
from inazuma.view.components.media_card.media_card import MediaPopup
from inazuma.view.components.auth_modal import AuthPopup
from kivy.logger import Logger
from inazuma.utility.data import themes_available
from typing import TYPE_CHECKING
from kivy.uix.settings import SettingOptions
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.settings import SettingSpacer
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.uix.popup import Popup

if TYPE_CHECKING:
    from kivy.uix.settings import Settings
    from viu_media.libs.media_api.types import MediaItem
    from viu_media.libs.provider.anime.types import Server


class SettingScrollOptions(SettingOptions):
    def _create_popup(self, instance):
        # global oORCA
        # create the popup

        content = GridLayout(cols=1, spacing="5dp")
        scrollview = ScrollView(do_scroll_x=False)
        scrollcontent = GridLayout(cols=1, spacing="5dp", size_hint=(None, None))
        scrollcontent.bind(minimum_height=scrollcontent.setter("height"))  # type: ignore
        self.popup = popup = Popup(
            content=content, title=self.title, size_hint=(0.5, 0.9), auto_dismiss=False
        )

        # we need to open the popup first to get the metrics
        popup.open()
        # Add some space on top
        content.add_widget(Widget(size_hint_y=None, height=dp(2)))
        # add all the options
        uid = str(self.uid)  # type: ignore
        for option in self.options:
            state = "down" if option == self.value else "normal"
            btn = ToggleButton(
                text=option,
                state=state,
                group=uid,
                size=(popup.width, dp(55)),
                size_hint=(None, None),
            )
            btn.bind(on_release=self._set_option)  # type: ignore
            scrollcontent.add_widget(btn)

        # finally, add a cancel button to return on the previous panel
        scrollview.add_widget(scrollcontent)
        content.add_widget(scrollview)
        content.add_widget(SettingSpacer())
        # btn = Button(text='Cancel', size=((oORCA.iAppWidth/2)-sp(25), dp(50)),size_hint=(None, None))
        btn = Button(text="Cancel", size=(popup.width, dp(50)), size_hint=(0.9, None))
        btn.bind(on_release=popup.dismiss)  # type: ignore
        content.add_widget(btn)


class Inazuma(MDApp):
    default_anime_image = resource_find(random.choice(["default_1.jpg", "default.jpg"]))
    default_banner_image = resource_find(random.choice(["banner_1.jpg", "banner.jpg"]))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        os.environ["VIU_APP_NAME"] = "inazuma"
        from inazuma.core.viu import Viu
        from viu_media.cli.config.loader import ConfigLoader

        self.viu_config = ConfigLoader().load()

        self.viu = Viu(self.viu_config)
        if "MEDIA_API_TOKEN" in os.environ:
            if not self.viu.media_api.is_authenticated():
                self.viu.media_api.authenticate(os.environ["MEDIA_API_TOKEN"])
        # self.icon = resource_find("logo.png")

        self.load_all_kv_files(self.directory)
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Lightcoral"
        self.manager_screens = ScreenManager()
        self.manager_screens.transition = FadeTransition()

        # Track active downloads by a unique key (media_id + episode)
        self.active_downloads = {}

    def build(self) -> ScreenManager:
        self.settings_cls = SettingsWithSidebar

        self.generate_application_screens()

        if config := self.config:
            if theme_color := config.get("Preferences", "theme_color"):
                self.theme_cls.primary_palette = theme_color
            if theme_style := config.get("Preferences", "theme_style"):
                self.theme_cls.theme_style = theme_style

        return self.manager_screens

    def on_start(self, *args):
        self.media_card_popup = MediaPopup()
        self.auth_popup = AuthPopup()

    def build_config(self, config):
        # General settings setup
        config.setdefaults(
            "Preferences",
            {
                "theme_color": "Cyan",
                "theme_style": "Dark",
                "downloads_dir": self.viu.config.downloads.downloads_dir,
            },
        )

        # Viu settings - dynamically extract from AppConfig
        viu_defaults = self._get_viu_config_defaults()
        config.setdefaults("Viu", viu_defaults)

    def _get_viu_config_defaults(self) -> dict:
        """Dynamically extract default values from viu.config (AppConfig)."""
        from enum import Enum

        defaults = {}
        viu_cfg = self.viu.config

        for section_name, section_model in viu_cfg:
            if section_name in ("fzf", "rofi"):
                continue
            for field_name in section_model.model_fields:
                value = getattr(section_model, field_name)
                # Convert enum to its value
                if isinstance(value, Enum):
                    value = value.value
                # Convert Path to string
                elif hasattr(value, "__fspath__"):
                    value = str(value)

                key = f"{section_name}_{field_name}"
                defaults[key] = value

        return defaults

    def _get_viu_settings(self) -> list:
        """Dynamically generate Kivy settings JSON from viu.config (AppConfig)."""
        import itertools

        viu_cfg = self.viu.config
        settings = []

        for section_name, section_model in viu_cfg:
            if section_name in ("fzf", "rofi"):
                continue

            # Add section title
            section_title = section_model.model_config.get(
                "title", section_name.replace("_", " ").title()
            )
            settings.append({"type": "title", "title": section_title})

            for field_name, field_info in itertools.chain(
                section_model.model_fields.items(),
                section_model.model_computed_fields.items(),
            ):
                field_type = getattr(field_info, "annotation", None) or getattr(
                    field_info, "return_type", None
                )
                field_value = getattr(section_model, field_name)

                # Skip None/unset fields
                if field_value is None:
                    continue

                # Determine Kivy setting type and options
                setting_type, options = self._get_kivy_setting_type(field_type)

                # Build the setting entry
                key = f"{section_name}_{field_name}"
                title = field_name.replace("_", " ").title()
                desc = field_info.description or ""

                setting_entry = {
                    "type": setting_type,
                    "title": title,
                    "desc": desc,
                    "section": "Viu",
                    "key": key,
                }

                if options:
                    setting_entry["options"] = options

                settings.append(setting_entry)

        return settings

    def _get_kivy_setting_type(self, field_type) -> tuple:
        """Map Pydantic field type to Kivy setting type and options."""
        from enum import Enum
        from pathlib import Path
        from typing import Literal, get_args, get_origin

        options = None

        # Check for Enum
        if (
            field_type is not None
            and isinstance(field_type, type)
            and issubclass(field_type, Enum)
        ):
            options = [member.value for member in field_type]
            return ("scrolloptions", options)

        # Check for Literal
        if get_origin(field_type) is Literal:
            args = get_args(field_type)
            if args:
                options = list(args)
                return ("scrolloptions", options)

        # Basic types
        if field_type is bool:
            return ("bool", None)
        if field_type in (int, float):
            return ("numeric", None)
        if field_type is Path or (
            hasattr(field_type, "__origin__") and field_type.__origin__ is Path
        ):
            return ("path", None)

        # Default to string
        return ("string", None)

    def build_settings(self, settings: "Settings"):
        settings.register_type("scrolloptions", SettingScrollOptions)
        app_settings = [
            {"type": "title", "title": "Preferences"},
            {
                "type": "scrolloptions",
                "title": "Theme Color",
                "desc": "Sets the theme color to be used for the app for more info on valid theme names refer to help",
                "section": "Preferences",
                "key": "theme_color",
                "options": themes_available,
            },
            {
                "type": "options",
                "title": "Theme Style",
                "desc": "Sets the app to dark or light theme",
                "section": "Preferences",
                "key": "theme_style",
                "options": ["Light", "Dark"],
            },
            {
                "type": "path",
                "title": "Downloads Directory",
                "desc": "location to download your videos",
                "section": "Preferences",
                "key": "downloads_dir",
            },
        ]
        viu_settings = self._get_viu_settings()

        settings.add_json_panel("Inazuma", self.config, data=json.dumps(app_settings))
        settings.add_json_panel("Viu", self.config, data=json.dumps(viu_settings))

    def on_config_change(self, config, section, key, value):
        if section == "Preferences":
            match key:
                case "theme_color":
                    if value in themes_available:
                        self.theme_cls.primary_palette = value
                    else:
                        Logger.warning(
                            "AniXStream Settings: An invalid theme has been entered and will be ignored"
                        )
                        config.set("Preferences", "theme_color", "Cyan")
                        config.write()
                case "theme_style":
                    self.theme_cls.theme_style = value

        elif section == "Viu":
            self._apply_viu_config_change(key, value)
            self._write_viu_config()
            self.viu.reset()

    def _write_viu_config(self):
        from viu_media.cli.config.generate import generate_config_toml_from_app_model
        from viu_media.core.constants import USER_CONFIG
        from viu_media.core.utils.file import AtomicWriter

        config_toml = generate_config_toml_from_app_model(self.viu.config)
        with AtomicWriter(USER_CONFIG, mode="w", encoding="utf-8") as f:
            f.write(config_toml)

    def _apply_viu_config_change(self, key: str, value):
        """Apply a config change to viu.config dynamically."""

        # Key format is "{section_name}_{field_name}"
        parts = key.split("_", 1)
        if len(parts) != 2:
            Logger.warning(f"Inazuma Settings: Invalid Viu config key format: {key}")
            return

        section_name, field_name = parts

        # Get the section model from viu.config
        if not hasattr(self.viu.config, section_name):
            Logger.warning(
                f"Inazuma Settings: Unknown Viu config section: {section_name}"
            )
            return

        section_model = getattr(self.viu.config, section_name)

        if not hasattr(section_model, field_name):
            Logger.warning(
                f"Inazuma Settings: Unknown field '{field_name}' in section '{section_name}'"
            )
            return

        # Get field info to determine the expected type
        field_info = section_model.model_fields.get(field_name)
        if not field_info:
            Logger.warning(
                f"Inazuma Settings: No field info for {section_name}.{field_name}"
            )
            return

        field_type = field_info.annotation

        # Convert the value to the appropriate type
        try:
            converted_value = self._convert_config_value(value, field_type)
            setattr(section_model, field_name, converted_value)
            Logger.info(
                f"Inazuma Settings: Updated {section_name}.{field_name} = {converted_value}"
            )
        except (ValueError, TypeError) as e:
            Logger.warning(
                f"Inazuma Settings: Failed to convert value for {section_name}.{field_name}: {e}"
            )

    def _convert_config_value(self, value, field_type):
        """Convert a config value string to the appropriate Python type."""
        from enum import Enum
        from pathlib import Path
        from typing import Literal, get_args, get_origin

        # Handle None
        if value is None or value == "":
            return None

        # Handle Enum types
        if (
            field_type is not None
            and isinstance(field_type, type)
            and issubclass(field_type, Enum)
        ):
            return field_type(value)

        # Handle Literal types
        if get_origin(field_type) is Literal:
            args = get_args(field_type)
            if value in args:
                return value
            raise ValueError(f"Value '{value}' not in Literal options: {args}")

        # Handle basic types
        if field_type is bool:
            if isinstance(value, bool):
                return value
            return value.lower() in ("true", "1", "yes", "on")

        if field_type is int:
            return int(value)

        if field_type is float:
            return float(value)

        if field_type is Path:
            return Path(value)

        # Default: return as string
        return str(value)

    def generate_application_screens(self) -> None:
        for i, name_screen in enumerate(screens.keys()):
            model = screens[name_screen]["model"](self.viu)
            controller = screens[name_screen]["controller"](model)
            view = controller.get_view()
            view.manager_screens = self.manager_screens
            view.name = name_screen
            self.manager_screens.add_widget(view)

    def search_for_anime(self, search_field, **kwargs):
        if self.manager_screens.current != "search screen":
            self.manager_screens.current = "search screen"
        search_screen = self.manager_screens.get_screen("search screen")
        search_screen.controller.handle_search_for_anime(search_field, **kwargs)

    def show_anime_screen(self, media_item: "MediaItem", caller_screen_name: str):
        self.manager_screens.current = anime_screen_name = "anime screen"
        self.manager_screens.get_screen(anime_screen_name).controller.update_anime_view(
            media_item, caller_screen_name
        )

    def play_on_external_player(
        self,
        url: str,
        episode: str,
        media_item: "MediaItem",
        server: "Server",
    ):
        from viu_media.libs.player.params import PlayerParams
        from threading import Thread

        episode_title = media_item.title.english + f"; Episode {episode}"
        player_thread = Thread(
            target=self.viu.player.play,
            args=(
                PlayerParams(
                    url=url,
                    title=episode_title,
                    episode=episode,
                    query=media_item.title.romaji or media_item.title.english,
                    headers=server.headers,
                ),
            ),
            daemon=True,
        )
        player_thread.start()

    #
    def download_media(
        self, url: str, episode: str, media_item: "MediaItem", server: "Server"
    ):
        from inazuma.utility.notification import show_notification
        from threading import Thread

        # Create unique identifier for this download task
        task_id = f"{media_item.id}_{episode}"

        # Check if already downloading
        if task_id in self.active_downloads:
            show_notification(
                "Download In Progress",
                f"{media_item.title.english}; Episode {episode} is already downloading",
            )
            return

        download_screen = self.manager_screens.get_screen("downloads screen")
        download_screen.controller.new_download_task(media_item, episode, server)

        # Mark as active
        self.active_downloads[task_id] = True

        # Create progress hook that includes task_id
        def progress_hook(data):
            download_screen.controller.on_episode_download_progress(task_id, data)

        download_thread = Thread(
            target=self._add_media_to_download_queue,
            args=(task_id, url, episode, media_item, server, [progress_hook]),
            daemon=True,
        )
        download_thread.start()

        show_notification(
            "New Download", f"{media_item.title.english}; Episode {episode}"
        )

    def _add_media_to_download_queue(
        self,
        task_id: str,
        url: str,
        episode: str,
        media_item: "MediaItem",
        server: "Server",
        progress_hooks=[],
    ):
        from viu_media.core.downloader import DownloadParams
        from inazuma.utility.notification import show_notification

        try:
            episode_title = f"{media_item.title.english}; Episode {episode}"
            download_result = self.viu.downloader.download(
                DownloadParams(
                    url=url,
                    anime_title=media_item.title.english,
                    episode_title=episode_title,
                    silent=True,
                    headers=server.headers,
                    progress_hooks=progress_hooks,
                    logger=Logger,
                )
            )

            # Handle completion
            if download_result:
                show_notification(
                    "Download Complete",
                    f"{media_item.title.english}; Episode {episode}",
                )

                # Update download screen to show completion
                download_screen = self.manager_screens.get_screen("downloads screen")
                download_screen.controller.on_download_complete(
                    task_id, download_result
                )
        except Exception as e:
            show_notification(
                "Download Failed",
                f"{media_item.title.english}; Episode {episode}: {str(e)}",
            )
            download_screen = self.manager_screens.get_screen("downloads screen")
            download_screen.controller.on_download_error(task_id, str(e))
        finally:
            # Remove from active downloads
            if task_id in self.active_downloads:
                del self.active_downloads[task_id]

    # def on_stop(self):
    #     pass
    #
    #
    # def add_anime_to_user_anime_list(self, id: int):
    #     updated_list = user_data_helper.get_user_anime_list()
    #     updated_list.append(id)
    #     user_data_helper.update_user_anime_list(updated_list)
    #
    # def remove_anime_from_user_anime_list(self, id: int):
    #     updated_list = user_data_helper.get_user_anime_list()
    #     if updated_list.count(id):
    #         updated_list.remove(id)
    #     user_data_helper.update_user_anime_list(updated_list)
    #


#
# def setup_app():
#     os.environ["KIVY_VIDEO"] = "ffpyplayer"  # noqa: E402
#     Config.set("graphics", "width", "1000")  # noqa: E402
#     Config.set("graphics", "minimum_width", "1000")  # noqa: E402
#     Config.set("kivy", "window_icon", resource_find("logo.ico"))  # noqa: E402
#     Config.write()  # noqa: E402
#
#     Loader.num_workers = 5
#     Loader.max_upload_per_frame = 10
#
#     resource_add_path(ASSETS_DIR)
#     resource_add_path(CONFIGS_DIR)
#
def main():
    Inazuma().run()
