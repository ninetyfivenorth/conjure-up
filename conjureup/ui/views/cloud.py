from ubuntui.utils import Padding
from ubuntui.widgets.hr import HR
from urwid import Text

from conjureup import events, juju
from conjureup.consts import CUSTOM_PROVIDERS, cloud_types
from conjureup.ui.views.base import BaseView
from conjureup.ui.widgets.selectors import MenuSelectButtonList


class CloudView(BaseView):
    title = "Choose a Cloud"
    subtitle = "Where would you like to deploy?"
    enabled_msg = 'Press [ENTER] to select this cloud, or use the ' \
                  'arrow keys to select another cloud.'
    default_disabled_msg = 'This cloud is disabled due to your selection of ' \
                           'spell or add-on. Please use the arrow keys to ' \
                           'select another cloud.'
    lxd_unavailable_msg = ("LXD not found, please install and wait "
                           "for this message to disappear:\n\n"
                           "  $ sudo snap install lxd\n"
                           "  $ sudo usermod -a -G lxd <youruser>\n"
                           "  $ newgrp lxd\n"
                           "  $ /snap/bin/lxd init")

    def __init__(self, app, public_clouds, custom_clouds,
                 compatible_cloud_types, cb=None, back=None):
        self.app = app
        self.cb = cb
        self.back = back
        self.public_clouds = public_clouds
        self.custom_clouds = custom_clouds
        self.compatible_cloud_types = compatible_cloud_types
        self.config = self.app.config
        self.buttons_pile_selected = False
        self.message = Text('')
        self._items_localhost_idx = None
        self.show_back_button = back is not None

        super().__init__()
        self.update_message()

    def after_keypress(self):
        self.update_message()

    def update_message(self):
        selected = self.widget.focus
        if selected.enabled:
            msg = self.enabled_msg
        else:
            msg = selected.user_data.get('disabled_msg',
                                         self.default_disabled_msg)
        self.set_footer(msg)

    def _enable_localhost_widget(self):
        """ Sets the proper widget for localhost availability
        """
        if self._items_localhost_idx is None:
            return
        self.widget.contents[self._items_localhost_idx][0].enabled = True
        self.update_message()

    def build_widget(self):
        widget = MenuSelectButtonList()
        default_selection = None
        cloud_types_by_name = juju.get_cloud_types_by_name()
        if len(self.public_clouds) > 0:
            widget.append(Text("Public Clouds"))
            widget.append(HR())
            for cloud_name in self.public_clouds:
                cloud_type = cloud_types_by_name[cloud_name]
                allowed = cloud_type in self.compatible_cloud_types
                if allowed and default_selection is None:
                    default_selection = len(widget.contents)
                widget.append_option(cloud_name, enabled=allowed)
            widget.append(Padding.line_break(""))
        if len(self.custom_clouds) > 0:
            widget.append(Text("Your Clouds"))
            widget.append(HR())
            for cloud_name in self.custom_clouds:
                cloud_type = cloud_types_by_name[cloud_name]
                allowed = cloud_type in self.compatible_cloud_types
                if allowed and default_selection is None:
                    default_selection = len(widget.contents)
                widget.append_option(cloud_name, enabled=allowed)
            widget.append(Padding.line_break(""))
        new_clouds = juju.get_compatible_clouds(CUSTOM_PROVIDERS)
        if new_clouds:
            lxd_allowed = cloud_types.LOCALHOST in self.compatible_cloud_types
            widget.append(Text("Configure a New Cloud"))
            widget.append(HR())
            for cloud_type in sorted(CUSTOM_PROVIDERS):
                if cloud_type == cloud_types.LOCALHOST and lxd_allowed:
                    self._items_localhost_idx = len(widget.contents)
                    if default_selection is None:
                        default_selection = len(widget.contents)
                    widget.append_option(
                        cloud_type,
                        enabled=events.LXDAvailable.is_set(),
                        user_data={
                            'disabled_msg': self.lxd_unavailable_msg,
                        })
                else:
                    allowed = cloud_type in self.compatible_cloud_types
                    if allowed and default_selection is None:
                        default_selection = len(widget.contents)
                    widget.append_option(cloud_type, enabled=allowed)

        widget.focus_position = default_selection or 2
        return widget

    def submit(self):
        if self.widget.selected:
            self.cb(self.widget.selected)

    def prev_screen(self):
        if self.back:
            self.back()
