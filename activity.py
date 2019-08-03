# Copyright (C) 2012 Cristhofer Travieso <cristhofert97@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import locale
import convert
import re

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import Gdk

from sugar3.activity import activity
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.radiotoolbutton import RadioToolButton

from gettext import gettext as _

SCREEN_WIDTH = Gdk.Screen.width()


class ConvertActivity(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle, True)

        self.max_participants = 1
        self.dic = {}

        # Canvas
        self._canvas = Gtk.VBox()

        hbox = Gtk.HBox()
        self._liststore = Gtk.ListStore(str)
        self.combo1 = Gtk.ComboBox.new_with_model_and_entry(self._liststore)
        cell = Gtk.CellRendererText()
        self.combo1.pack_start(cell, True)
        self.combo1.set_entry_text_column(0)
        self.combo1.connect('changed', self._update_labels)

        flip_btn = Gtk.Button()
        flip_btn.connect('clicked', self._flip)
        flip_btn.set_tooltip_text("Flip Units")
        flip_btn.add(Gtk.Image.new_from_file('icons/flip.svg'))

        self.combo2 = Gtk.ComboBox.new_with_model_and_entry(self._liststore)
        cell = Gtk.CellRendererText()
        self.combo2.pack_start(cell, True)
        self.combo2.set_entry_text_column(0)
        self.combo2.connect('changed', self._update_labels)

        self.label_box = Gtk.HBox()

        self.value_entry = Gtk.Entry()
        self.value_entry.set_placeholder_text("Enter number")
        self.value_entry.connect('insert-text', self._value_insert_text)
        self.value_entry.connect('changed', self._update_labels)

        self.label = Gtk.Label()
        self.label.set_selectable(True)
        self.label._size = 12
        self.label.connect('draw', self.resize_label)

        self.ratio_label = Gtk.Label()
        self.ratio_label.set_selectable(True)
        self.ratio_label.connect('draw', self.resize_label)

        self._canvas.pack_start(hbox, False, False, 20)
        hbox.pack_start(self.combo1, False, True, 20)
        hbox.pack_start(flip_btn, True, False, 20)
        hbox.pack_end(self.combo2, False, True, 20)
        value_box = Gtk.HBox()
        convert_box = Gtk.HBox()
        convert_box.pack_start(value_box, True, False, 0)
        value_box.pack_start(self.value_entry, False, False, 0)
        self._canvas.pack_start(convert_box, False, False, 5)
        self._canvas.pack_start(self.ratio_label, False, False, 10)
        self._canvas.pack_start(self.label_box, True, False, 0)
        self.label_box.add(self.label)

        self.set_canvas(self._canvas)

        # Toolbar
        toolbarbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)

        toolbarbox.toolbar.insert(activity_button, 0)

        separator = Gtk.SeparatorToolItem()
        separator.set_expand(False)
        separator.set_draw(True)
        toolbarbox.toolbar.insert(separator, -1)

        # RadioToolButton
        self._length_btn = RadioToolButton()
        self._length_btn.connect('clicked',
                                 lambda w: self._update_combo(convert.length))
        # TRANS: https://en.wikipedia.org/wiki/Length
        self._length_btn.set_tooltip(_('Length'))
        self._length_btn.props.icon_name = 'length'

        self._volume_btn = RadioToolButton()
        self._volume_btn.connect('clicked',
                                 lambda w: self._update_combo(convert.volume))
        # TRANS: https://en.wikipedia.org/wiki/Volume
        self._volume_btn.set_tooltip(_('Volume'))
        self._volume_btn.props.icon_name = 'volume'
        self._volume_btn.props.group = self._length_btn

        self._area_btn = RadioToolButton()
        self._area_btn.connect('clicked',
                               lambda w: self._update_combo(convert.area))
        # TRANS: https://en.wikipedia.org/wiki/Area
        self._area_btn.set_tooltip(_('Area'))
        self._area_btn.props.icon_name = 'area'
        self._area_btn.props.group = self._length_btn

        self._weight_btn = RadioToolButton()
        self._weight_btn.connect('clicked',
                                 lambda w: self._update_combo(convert.weight))
        # TRANS: https://en.wikipedia.org/wiki/Weight
        self._weight_btn.set_tooltip(_('Weight'))
        self._weight_btn.props.icon_name = 'weight'
        self._weight_btn.props.group = self._length_btn

        self._speed_btn = RadioToolButton()
        self._speed_btn.connect('clicked',
                                lambda w: self._update_combo(convert.speed))
        # TRANS: https://en.wikipedia.org/wiki/Speed
        self._speed_btn.set_tooltip(_('Speed'))
        self._speed_btn.props.icon_name = 'speed'
        self._speed_btn.props.group = self._length_btn

        self._time_btn = RadioToolButton()
        self._time_btn.connect('clicked',
                               lambda w: self._update_combo(convert.time))
        # TRANS: https://en.wikipedia.org/wiki/Time
        self._time_btn.set_tooltip(_('Time'))
        self._time_btn.props.icon_name = 'time'
        self._time_btn.props.group = self._length_btn

        self._temp_btn = RadioToolButton()
        self._temp_btn.connect('clicked',
                               lambda w: self._update_combo(convert.temp))
        # TRANS: https://en.wikipedia.org/wiki/Temperature
        self._temp_btn.set_tooltip(_('Temperature'))
        self._temp_btn.props.icon_name = 'temp'
        self._temp_btn.props.group = self._length_btn

        #Circle
        self._circle_btn = RadioToolButton()
        self._circle_btn.connect('clicked',
                               lambda w: self._update_combo(convert.circle))
        self._circle_btn.set_tooltip(_('Angles of Circles'))
        self._circle_btn.props.icon_name = 'circle'
        self._circle_btn.props.group = self._length_btn

        #pressure
        self._pressure_btn = RadioToolButton()
        self._pressure_btn.connect('clicked',
                               lambda w: self._update_combo(convert.pressure))
        self._pressure_btn.set_tooltip(_('Pressure'))
        self._pressure_btn.props.icon_name = 'pressure'
        self._pressure_btn.props.group = self._length_btn

        #force
        self._force_btn = RadioToolButton()
        self._force_btn.connect('clicked',
                               lambda w: self._update_combo(convert.force))
        self._force_btn.set_tooltip(_('Force'))
        self._force_btn.props.icon_name = 'force'
        self._force_btn.props.group = self._length_btn

        #energy
        self._energy_btn = RadioToolButton()
        self._energy_btn.connect('clicked',
                               lambda w: self._update_combo(convert.energy))
        self._energy_btn.set_tooltip(_('Energy'))
        self._energy_btn.props.icon_name = 'energy'
        self._energy_btn.props.group = self._length_btn

        #Storage
        self._storage_btn = RadioToolButton()
        self._storage_btn.connect('clicked',
                               lambda w: self._update_combo(convert.storage))
        self._storage_btn.set_tooltip(_('Digital Storage'))
        self._storage_btn.props.icon_name = 'storage'
        self._storage_btn.props.group = self._length_btn
        


        toolbarbox.toolbar.insert(self._length_btn, -1)
        toolbarbox.toolbar.insert(self._volume_btn, -1)
        toolbarbox.toolbar.insert(self._area_btn, -1)
        toolbarbox.toolbar.insert(self._weight_btn, -1)
        toolbarbox.toolbar.insert(self._speed_btn, -1)
        toolbarbox.toolbar.insert(self._time_btn, -1)
        toolbarbox.toolbar.insert(self._temp_btn, -1)
        toolbarbox.toolbar.insert(self._circle_btn, -1)
        toolbarbox.toolbar.insert(self._pressure_btn, -1)
        toolbarbox.toolbar.insert(self._force_btn, -1)
        toolbarbox.toolbar.insert(self._energy_btn, -1)
        toolbarbox.toolbar.insert(self._storage_btn, -1)
        

        separator = Gtk.SeparatorToolItem()
        separator.set_expand(True)
        separator.set_draw(False)
        toolbarbox.toolbar.insert(separator, -1)

        stopbtn = StopButton(self)
        toolbarbox.toolbar.insert(stopbtn, -1)

        self.set_toolbar_box(toolbarbox)
        self._update_combo(convert.length)
        self.show_all()

    def format_values(self, value):
        decimals = str(len(value.split('.')[-1]))
        fmt = '%.' + decimals + 'f'
        new_value = locale.format(fmt, float(value))
        new_value = new_value.rstrip("0")
        if new_value[-1] == '.':
            new_value = new_value[0:len(new_value)-1]
        return new_value

    def _update_ratio_label(self):
        try:
            num_value = '1'
            new_value = self.format_values(num_value)

            convert_value = str(self.convert(float(num_value)))
            new_convert = self.format_values(convert_value)

            text = '%s %s ~ %s %s' % (new_value, self._get_active_text(self.combo1), new_convert, self._get_active_text(self.combo2))
            self.ratio_label.set_text(text)
        except ValueError:
            pass

    def _update_labels(self, entry):
        self._update_conversion_label(entry)
        self._update_ratio_label()

    def _update_conversion_label(self, entry):
        try:
            num_value = str(self.value_entry.get_text())
            num_value = str(num_value.replace(',', ''))
            new_value = self.format_values(num_value)

            convert_value = str(self.convert(float(num_value)))
            new_convert = self.format_values(convert_value)

            text = '%s ~ %s' % (new_value, new_convert)
            self.label.set_text(text)
        except ValueError:
            pass

    def _update_combo(self, data):
        self._liststore.clear()
        self.dic = data
        keys = self.dic.keys()
        keys.sort()
        for x in keys:
            self._liststore.append(['%s' % (x)])
        if keys[0] == 'Cables':
            self.combo1.set_active(12)
            self.combo2.set_active(12)
        elif keys[0] == 'Cubic Centimeter':
            self.combo1.set_active(3)
            self.combo2.set_active(3)
        elif keys[0] == 'Acre':
            self.combo1.set_active(4)
            self.combo2.set_active(4)
        elif keys[0] == 'Carat':
            self.combo1.set_active(2)
            self.combo2.set_active(2)
        elif keys[0] == 'Centimeters/Minute':
            self.combo1.set_active(9)
            self.combo2.set_active(9)
        elif keys[0] == 'Day':
            self.combo1.set_active(8)
            self.combo2.set_active(8)
        elif keys[0] == 'Celsius':
            self.combo1.set_active(2)
            self.combo2.set_active(2)
        elif keys[0] == 'Degrees':
            self.combo1.set_active(1)
            self.combo2.set_active(1)
        elif keys[0] == 'Atmosphere (atm)':
            self.combo1.set_active(2)
            self.combo2.set_active(2)
        elif keys[0] == 'Dyne (dyn)':
            self.combo1.set_active(2)
            self.combo2.set_active(2)
        elif keys[0] == 'Calories (cal)':
            self.combo1.set_active(2)
            self.combo2.set_active(2)
        elif keys[0] == 'Bit':
            self.combo1.set_active(1)
            self.combo2.set_active(1)
        else:
            pass
        self.show_all()

    def _get_active_text(self, combobox):
        active = combobox.get_active()
        keys = self.dic.keys()
        keys.sort()
        if active < 0:
            active = 0
        text = keys[active]
        if '<sup>' in text:
            text = text.split('<b>')[1].split('</b>')[0]
        return text

    def _flip(self, widget):
        value = self.label.get_text().split(' ~ ')
        self.value_entry.set_text(value[1])
        active_combo1 = self.combo1.get_active()
        active_combo2 = self.combo2.get_active()
        self.combo1.set_active(active_combo2)
        self.combo2.set_active(active_combo1)
        
        


    def resize_label(self, widget, event):
        num_label = len(self.label.get_text())
        try:
            size = str((60 * SCREEN_WIDTH / 100) / num_label)
            if not size == self.label._size:
                self.label.modify_font(Pango.FontDescription(size))
                self.label._size = size
        except ZeroDivisionError:
            pass

    def convert(self, number):
        unit = self._get_active_text(self.combo1)
        to_unit = self._get_active_text(self.combo2)
        return convert.convert(number, unit, to_unit, self.dic)

    def _value_insert_text(self, entry, text, length, position):
        for char in text:
            if char == "-" and \
               self.value_entry.get_text() is "" and len(text) == 1:
                return False
            elif not re.match('[0-9,.]', char):
                entry.emit_stop_by_name('insert-text')
                return True
        return False

