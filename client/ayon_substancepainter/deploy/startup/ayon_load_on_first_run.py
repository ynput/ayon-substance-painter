"""Ease the AYON on-boarding process by loading the plug-in on first run"""
import logging

AYON_PLUGIN_NAME = "ayon_plugin"

log = logging.getLogger(__name__)


def start_plugin():
    try:
        # This isn't exposed in the official API so we keep it in a try-except
        from painter_plugins_ui import (
            get_settings,
            LAUNCH_AT_START_KEY,
            ON_STATE,
            plugin_manager
        )
        try:
            # Substance Painter >=12.0
            from painter_plugins_ui import _PLUGINS_MENU as PLUGINS_MENU
        except ImportError:
            # Substance Painter <12.0
            from painter_plugins_ui import PLUGINS_MENU

        # The `painter_plugins_ui` plug-in itself is also a startup plug-in
        # we need to take into account that it could run either earlier or
        # later than this startup script, we check whether its menu initialized
        is_before_plugins_menu = PLUGINS_MENU is None

        settings = get_settings(AYON_PLUGIN_NAME)
        if settings.value(LAUNCH_AT_START_KEY, None) is None:
            print("Initializing AYON plug-in on first run...")
            if is_before_plugins_menu:
                print("- running before 'painter_plugins_ui'")
                # Delay the launch to the painter_plugins_ui initialization
                settings.setValue(LAUNCH_AT_START_KEY, ON_STATE)
            else:
                # Launch now
                print("- running after 'painter_plugins_ui'")
                plugin_manager(AYON_PLUGIN_NAME)(True)

                # Set the checked state in the menu to avoid confusion
                action = next(action for action in PLUGINS_MENU._menu.actions()
                              if action.text() == AYON_PLUGIN_NAME)
                if action is not None:
                    action.blockSignals(True)
                    action.setChecked(True)
                    action.blockSignals(False)
        else:
            print(
                "AYON plug-in is explicitly disabled by user. To enable it,"
                " please load 'ayon_plugin' in the Python menu."
            )

    except Exception:
        log.error("Unable to auto-load AYON plug-in", exc_info=True)
