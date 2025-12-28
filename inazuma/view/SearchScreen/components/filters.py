from datetime import datetime
from typing import TYPE_CHECKING

from kivy.properties import DictProperty, NumericProperty, ObjectProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.dropdownitem import MDDropDownItem
from kivymd.uix.menu import MDDropdownMenu
from viu_media.libs.media_api.types import MediaGenre, MediaSort, MediaTag

if TYPE_CHECKING:
    from inazuma.controller.search_screen import SearchScreenController

# Generate year range dynamically from 1990 to current year + 1
YEARS = [str(year) for year in range(datetime.now().year + 1, 1989, -1)]

# Available per_page options
PER_PAGE_OPTIONS = [10, 20, 30, 40, 50]

# Human-readable labels for filter values
FILTER_LABELS = {
    "sort": {
        "SEARCH_MATCH": "Best Match",
        "POPULARITY_DESC": "Most Popular",
        "TRENDING_DESC": "Trending",
        "SCORE_DESC": "Highest Rated",
        "FAVOURITES_DESC": "Most Favorited",
        "START_DATE_DESC": "Newest",
        "START_DATE": "Oldest",
        "TITLE_ENGLISH": "Title (A-Z)",
        "TITLE_ENGLISH_DESC": "Title (Z-A)",
        "EPISODES_DESC": "Most Episodes",
    },
    "status": {
        "RELEASING": "Currently Airing",
        "FINISHED": "Finished",
        "NOT_YET_RELEASED": "Not Yet Released",
        "CANCELLED": "Cancelled",
        "HIATUS": "On Hiatus",
    },
    "genre": {g: g.replace("_", " ").title() for g in MediaGenre.__members__.keys()},
    "tag": {t: t.replace("_", " ").title() for t in MediaTag.__members__.keys()},
    "format": {
        "TV": "TV Series",
        "TV_SHORT": "TV Short",
        "MOVIE": "Movie",
        "SPECIAL": "Special",
        "OVA": "OVA",
        "ONA": "ONA",
        "MUSIC": "Music Video",
    },
    "season": {
        "WINTER": "Winter (Jan-Mar)",
        "SPRING": "Spring (Apr-Jun)",
        "SUMMER": "Summer (Jul-Sep)",
        "FALL": "Fall (Oct-Dec)",
    },
}

DEFAULT_FILTERS = {
    "sort": MediaSort.SEARCH_MATCH.value,
    "status": "DISABLED",
    "genre": "DISABLED",
    "tag": "DISABLED",
    "format": "DISABLED",
    "season": "DISABLED",
    "year": "DISABLED",
}


class FilterDropDown(MDDropDownItem):
    text: str = StringProperty()


class FilterChip(MDBoxLayout):
    """A filter chip with label and dropdown."""

    label: str = StringProperty()
    filter_name: str = StringProperty()
    value: str = StringProperty("DISABLED")


class Filters(MDBoxLayout):
    controller: "SearchScreenController" = ObjectProperty()
    filters: dict = DictProperty(DEFAULT_FILTERS.copy())
    per_page: int = NumericProperty(30)

    def on_kv_post(self, base_widget):
        """Initialize per_page from config after KV is loaded."""
        app = MDApp.get_running_app()
        if app and hasattr(app, "viu"):
            self.per_page = app.viu.config.anilist.per_page

    def get_display_text(self, filter_name: str, value: str) -> str:
        """Get human-readable display text for a filter value."""
        if value == "DISABLED":
            return "Any"
        labels = FILTER_LABELS.get(filter_name, {})
        return labels.get(value, value.replace("_", " ").title())

    def open_filter_menu(self, menu_item, filter_name):
        items = []
        match filter_name:
            case "sort":
                # Show only common sort options for cleaner UX
                items = list(FILTER_LABELS["sort"].keys())
            case "status":
                items = list(FILTER_LABELS["status"].keys())
                items.insert(0, "DISABLED")
            case "genre":
                items = [f for f in MediaGenre.__members__.keys()]
                items.insert(0, "DISABLED")
            case "tag":
                items = [t for t in MediaTag.__members__.keys()]
                items.insert(0, "DISABLED")
            case "format":
                items = list(FILTER_LABELS["format"].keys())
                items.insert(0, "DISABLED")
            case "season":
                items = list(FILTER_LABELS["season"].keys())
                items.insert(0, "DISABLED")
            case "year":
                items = YEARS.copy()
                items.insert(0, "DISABLED")
            case "per_page":
                # Handle per_page separately with numeric values
                menu_items = [
                    {
                        "text": str(val),
                        "on_release": lambda v=val: self._set_per_page(v),
                    }
                    for val in PER_PAGE_OPTIONS
                ]
                MDDropdownMenu(caller=menu_item, items=menu_items).open()
                return
            case _:
                items = []
        if items:
            menu_items = [
                {
                    "text": self.get_display_text(filter_name, item),
                    "on_release": lambda filter_value=item: self._filter_menu_callback(
                        filter_name, filter_value
                    ),
                }
                for item in items
            ]
            MDDropdownMenu(caller=menu_item, items=menu_items).open()

    def _filter_menu_callback(self, filter_name, filter_value):
        display_text = self.get_display_text(filter_name, filter_value)
        match filter_name:
            case "sort":
                self.ids.sort_filter.text = display_text
                self.filters["sort"] = filter_value
            case "status":
                self.ids.status_filter.text = display_text
                self.filters["status"] = filter_value
            case "genre":
                self.ids.genre_filter.text = display_text
                self.filters["genre"] = filter_value
            case "tag":
                self.ids.tag_filter.text = display_text
                self.filters["tag"] = filter_value
            case "format":
                self.ids.format_filter.text = display_text
                self.filters["format"] = filter_value
            case "season":
                self.ids.season_filter.text = display_text
                self.filters["season"] = filter_value
            case "year":
                self.ids.year_filter.text = display_text
                self.filters["year"] = filter_value

    def _set_per_page(self, value: int):
        """Set per_page in config and update UI."""
        self.per_page = value
        self.ids.per_page_filter.text = str(value)
        
        # Update the viu config
        app = MDApp.get_running_app()
        if app and hasattr(app, "viu"):
            app.viu.config.anilist.per_page = value

    def reset_filters(self):
        """Reset all filters to default values."""
        self.filters = DEFAULT_FILTERS.copy()
        self.ids.sort_filter.text = self.get_display_text("sort", self.filters["sort"])
        self.ids.status_filter.text = self.get_display_text(
            "status", self.filters["status"]
        )
        self.ids.genre_filter.text = self.get_display_text(
            "genre", self.filters["genre"]
        )
        self.ids.tag_filter.text = self.get_display_text("tag", self.filters["tag"])
        self.ids.format_filter.text = self.get_display_text(
            "format", self.filters["format"]
        )
        self.ids.season_filter.text = self.get_display_text(
            "season", self.filters["season"]
        )
        self.ids.year_filter.text = self.get_display_text("year", self.filters["year"])

    def has_active_filters(self) -> bool:
        """Check if any filter (other than sort) is active."""
        return any(
            v != "DISABLED"
            for k, v in self.filters.items()
            if k not in ["sort", "page"]
        )

    def apply_filters(self):
        """Trigger search with current filters."""
        if self.controller:
            self.controller.apply_filters()
