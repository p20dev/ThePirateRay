"""Packaged GTK presentation for PirateRay import preflight results."""

from gettext import gettext as _

from gi.repository import Adw, Gio

from rayforge.core.hooks import hookimpl
from rayforge.ui_gtk.action_registry import MenuPlacement, action_registry
from rayforge.ui_gtk.actions import action_extension_registry

from .import_preflight import inspect_imported_workflow
from .preflight_presentation import format_preflight_report


ADDON_NAME = "the_pirate_ray_jcz"
ACTION_NAME = "pirateray-import-preflight"


def _register_actions(action_manager):
    action = Gio.SimpleAction.new(ACTION_NAME, None)

    def on_activate(_action, _parameter):
        report = inspect_imported_workflow(action_manager.doc)
        presentation = format_preflight_report(report)
        dialog = Adw.MessageDialog(
            transient_for=action_manager.win,
            heading=presentation["heading"],
            body=presentation["body"],
        )
        dialog.add_response("close", _("Close"))
        dialog.set_default_response("close")
        dialog.set_close_response("close")
        dialog.present()

    action.connect("activate", on_activate)
    action_manager.win.add_action(action)
    action_manager.actions[ACTION_NAME] = action
    action_registry.register(
        action_name=ACTION_NAME,
        action=action,
        addon_name=ADDON_NAME,
        label=_("PirateRay Import Preflight"),
        menu=MenuPlacement(menu_id="tools", priority=60),
    )


@hookimpl
def register_actions(_action_registry):
    """Expose the read-only preflight report in Rayforge's Tools menu."""
    action_extension_registry.register_setup(_register_actions, ADDON_NAME)
