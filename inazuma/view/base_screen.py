from kivy.properties import (
    ObjectProperty,
    StringProperty,
    NumericProperty,
    BooleanProperty,
)
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.navigationrail import MDNavigationRail, MDNavigationRailItem
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.tooltip import MDTooltip

from ..utility.observer import Observer


# Breakpoint for mobile layout (in dp)
MOBILE_BREAKPOINT = 768


class NavRail(MDNavigationRail):
    screen = ObjectProperty()


class BottomNav(MDNavigationBar):
    """Bottom navigation bar for mobile screens."""

    screen = ObjectProperty()


class BottomNavItem(MDNavigationItem):
    """Bottom navigation item with icon and text."""

    icon = StringProperty()
    text = StringProperty()


class SearchBar(MDBoxLayout):
    screen = ObjectProperty()


class Tooltip(MDTooltip):
    pass


class TooltipMDIconButton(Tooltip, MDIconButton):
    tooltip_text = StringProperty()


class CommonNavigationRailItem(MDNavigationRailItem):
    icon = StringProperty()
    text = StringProperty()


class HeaderLabel(MDBoxLayout):
    text = StringProperty()
    halign = StringProperty("left")


class BaseScreenView(MDScreen, Observer):
    """
    A base class that implements a visual representation of the model data.
    The view class must be inherited from this class.
    """

    controller = ObjectProperty()
    """
    controller object - :class:`~controller.controller_screen.ClassScreenControler`.

    :attr:`controller` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    model = ObjectProperty()
    """
    model object - :class:`~model.model_screen.ClassScreenModel`.

    :attr:`model` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    manager_screens = ObjectProperty()
    """
    Screen manager object - :class:`~kivymd.uix.screenmanager.MDScreenManager`.

    :attr:`manager_screens` is an :class:`~kivy.properties.ObjectProperty`
    and defaults to `None`.
    """

    is_mobile = BooleanProperty(False)
    """
    Property to track if the current window size is mobile/small.
    Updated automatically on window resize.
    
    :attr:`is_mobile` is a :class:`~kivy.properties.BooleanProperty`
    and defaults to `False`.
    """

    mobile_breakpoint = NumericProperty(MOBILE_BREAKPOINT)
    """
    The width threshold (in dp) below which the layout switches to mobile mode.
    
    :attr:`mobile_breakpoint` is a :class:`~kivy.properties.NumericProperty`
    and defaults to `600`.
    """

    def __init__(self, **kw):
        super().__init__(**kw)
        # Often you need to get access to the application object from the view
        # class. You can do this using this attribute.
        from .. import Inazuma

        self.app: Inazuma = MDApp.get_running_app()  # type: ignore
        # Adding a view class as observer.
        self.model.add_observer(self)

        # Set up responsive layout tracking
        from kivy.core.window import Window
        from kivy.clock import Clock

        Window.bind(on_resize=self._on_window_resize)
        Clock.schedule_once(lambda dt: self._check_layout(Window.width))

    def _on_window_resize(self, window, width, height):
        """Handle window resize to update mobile/desktop layout."""
        self._check_layout(width)

    def _check_layout(self, width):
        """Check if layout should switch between mobile and desktop."""
        from kivy.metrics import dp

        self.is_mobile = width < dp(self.mobile_breakpoint)
