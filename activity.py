# -*- coding: utf-8 -*-
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
import json

import gi
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk
from gi.repository import Pango

from sugar3.activity import activity
from sugar3.activity.widgets import StopButton
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.graphics.radiotoolbutton import RadioToolButton
from sugar3.graphics.style import FONT_SIZE, FONT_FACE

from gettext import gettext as _


class Conversion(Gtk.Label):
    def __init__(self):
        Gtk.Label.__init__(self)
        self.set_selectable(True)
        self.modify_font(Pango.FontDescription(
                       '%s %d' % (FONT_FACE, int(FONT_SIZE * 1.2))))


class Result(Gtk.Label):
    def __init__(self):
        Gtk.Label.__init__(self)
        self.set_selectable(True)
        self._size = -1

    def set_text(self, text):
        Gtk.Label.set_text(self, text)
        length = len(text)
        if length == 0:
            return

        width = self.get_allocation().width
        size = (60 * width / 100) / length + int(FONT_SIZE * 1.2)
        if not size == self._size:
            self.modify_font(Pango.FontDescription(
                '%s %d' % (FONT_FACE, size)))
            self._size = size


class ConvertActivity(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle, True)

        self.max_participants = 1
        self.units = {}

        self._liststore = Gtk.ListStore(str)

        self.label1 = Gtk.Label()
        self.label1.set_markup('<big>From value</big>')
        self.label2 = Gtk.Label()
        self.label2.set_markup('<big>From unit</big>')
        self.label3 = Gtk.Label()
        self.label3.set_markup('<big>To value</big>')
        self.label4 = Gtk.Label()
        self.label4.set_markup('<big>To unit</big>')

        u_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        u_hbox.pack_start(self.label1, True, True, 5)
        u_hbox.pack_start(self.label2, True, True, 20)
        u_hbox.pack_start(self.label3, True, True, 20)
        u_hbox.pack_start(self.label4, True, True, 5)

        arrow_font = Pango.FontDescription(
            '%s %d' % (FONT_FACE, int(FONT_SIZE * 1.8)))
        input_font = Pango.FontDescription(
            '%s %d' % (FONT_FACE, int(FONT_SIZE * 1.2)))

        self.from_value = Gtk.Entry()
        self.from_value.set_placeholder_text("Enter value")
        self.from_value.connect('insert-text', self._insert_text_cb)
        self.from_value.connect('changed', self._from_changed_cb)
        self.from_value.override_font(input_font)

        self.from_unit = Gtk.ComboBox.new_with_model_and_entry(self._liststore)
        self.from_unit.pack_start(Gtk.CellRendererText(), True)
        self.from_unit.set_entry_text_column(0)
        self.from_unit.set_id_column(0)
        self.from_unit.connect('changed', self._from_changed_cb)
        self.from_unit.override_font(input_font)

        self.arrow = Gtk.Label()
        self.arrow.override_font(arrow_font)
        self.arrow.set_text("→")

        self.to_value = Gtk.Entry()
        self.to_value.connect('insert-text', self._insert_text_cb)
        self.to_value.connect('changed', self._to_changed_cb)
        self.to_value.override_font(input_font)

        self.to_unit = Gtk.ComboBox.new_with_model_and_entry(self._liststore)
        self.to_unit.pack_start(Gtk.CellRendererText(), True)
        self.to_unit.set_entry_text_column(0)
        self.to_unit.set_id_column(0)
        self.to_unit.connect('changed', self._to_changed_cb)
        self.to_unit.override_font(input_font)

        l_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        l_hbox.pack_start(self.from_value, True, True, 5)
        l_hbox.pack_start(self.from_unit, True, True, 5)
        l_hbox.pack_start(self.arrow, False, False, 15)
        l_hbox.pack_start(self.to_value, True, True, 5)
        l_hbox.pack_end(self.to_unit, True, True, 5)

        self.result = Result()
        self.conversion = Conversion()

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.pack_start(u_hbox, False, False, 30)
        box.pack_start(l_hbox, False, False, 0)
        box.pack_start(self.conversion, False, False, 20)
        box.pack_start(self.result, True, False, 0)
        self.set_canvas(box)

        # Toolbar
        toolbarbox = ToolbarBox()

        activity_button = ActivityToolbarButton(self)

        toolbarbox.toolbar.insert(activity_button, 0)

        separator = Gtk.SeparatorToolItem()
        separator.set_expand(False)
        separator.set_draw(True)
        toolbarbox.toolbar.insert(separator, -1)

        self.dimensions = {}
        for name in convert.dimensions:
            button = RadioToolButton()
            button.set_tooltip(convert.dimension_tooltips[name])
            button.props.icon_name = name
            if len(self.dimensions) > 0:
                button.props.group = self.dimensions['length']
            button.connect('clicked', self._set_dimension, name)
            toolbarbox.toolbar.insert(button, -1)
            self.dimensions[name] = button

        separator = Gtk.SeparatorToolItem()
        separator.set_expand(True)
        separator.set_draw(False)
        toolbarbox.toolbar.insert(separator, -1)

        stopbtn = StopButton(self)
        toolbarbox.toolbar.insert(stopbtn, -1)

        self.set_toolbar_box(toolbarbox)
        self._set_dimension(None, 'length')
        self._update_conversion(direction='from')
        self.show_all()

    def _from_changed_cb(self, widget):
        direction = 'from'
        if isinstance(widget, Gtk.Entry):
            self._update_value(widget, direction)
        elif isinstance(widget, Gtk.ComboBox):
            if self.arrow.get_text() == '←':
                direction = 'to'
            self._update_unit(widget, direction)
            self._update_conversion(direction)

    def _to_changed_cb(self, widget):
        direction = 'to'
        if isinstance(widget, Gtk.Entry):
            self._update_value(widget, direction)
        elif isinstance(widget, Gtk.ComboBox):
            if self.arrow.get_text() == '→':
                direction = 'from'
            self._update_unit(widget, direction)
            self._update_conversion(direction)

    def _update_value(self, entry, direction):
        try:
            num_value = str(entry.get_text())
            num_value = float(num_value.replace(',', ''))
            new_value = self._format_values(num_value)
            convert_value = str(self._convert(num_value, direction))
            new_convert = self._format_values(convert_value)
            self._update_result(new_value, new_convert, direction)
            self._update_conversion(direction)

        except ValueError:
            self._update_result('', '', direction)
            self._update_conversion(direction)

    def _update_conversion(self, direction):
        value = self._format_values('1')
        convert = self._format_values(str(self._convert(float(value), direction)))
        text = self.conversion.get_text()
        if direction == 'from':
            if convert != '' and value != '':
                text = '%s %s : %s %s' % (
                    value, self._get_active_text(self.from_unit),
                    convert, self._get_active_text(self.to_unit))
            else:
                pass
        elif direction == 'to':
            if convert != '' and value != '':
                text = '%s %s : %s %s' % (
                    convert, self._get_active_text(self.from_unit),
                    value, self._get_active_text(self.to_unit))
            else:
                pass
        self.conversion.set_text(text)

    def _format_values(self, value):
        decimals = str(len(str(value).split('.')[-1]))
        fmt = '%.' + decimals + 'f'
        new_value = locale.format(fmt, float(value))
        new_value = new_value.rstrip("0")
        if new_value[-1] == '.':
            new_value = new_value[0:len(new_value) - 1]
        return new_value

    def _update_unit(self, combo, direction):
        if direction == 'from':
            self._update_value(self.from_value, direction)
        elif direction == 'to':
            self._update_value(self.to_value, direction)

    def _update_result(self, new_value, new_convert, direction):
        if direction == 'from':
            self.to_value.handler_block_by_func(self._to_changed_cb)
            self.to_value.handler_block_by_func(self._insert_text_cb)
            self.to_value.set_text(new_convert)
            self.to_value.handler_unblock_by_func(self._insert_text_cb)
            self.to_value.handler_unblock_by_func(self._to_changed_cb)

            self.arrow.set_text("→")
            self.label1.set_markup('<big>From value</big>')
            self.label2.set_markup('<big>From unit</big>')
            self.label3.set_markup('<big>To value</big>')
            self.label4.set_markup('<big>To unit</big>')
            if new_convert != '' and new_value != '':
                text = '%s %s ~ %s %s' % (
                    new_value, self._get_active_text(self.from_unit),
                    new_convert, self._get_active_text(self.to_unit))
                self.result.set_text(text)
            else:
                self.result.set_text('')

        elif direction == 'to':
            self.from_value.handler_block_by_func(self._from_changed_cb)
            self.from_value.handler_block_by_func(self._insert_text_cb)
            self.from_value.set_text(new_convert)
            self.from_value.handler_unblock_by_func(self._insert_text_cb)
            self.from_value.handler_unblock_by_func(self._from_changed_cb)

            self.arrow.set_text("←")
            self.label1.set_markup('<big>To value</big>')
            self.label2.set_markup('<big>To unit</big>')
            self.label3.set_markup('<big>From value</big>')
            self.label4.set_markup('<big>From unit</big>')
            if new_convert != '' and new_value != '':
                text = '%s %s ~ %s %s' % (
                    new_convert, self._get_active_text(self.from_unit),
                    new_value, self._get_active_text(self.to_unit))
                self.result.set_text(text)
            else:
                self.result.set_text('')

    def _set_dimension(self, widget, name):
        self.dimension = name

        self.units = convert.dimension_units[name]
        keys = list(self.units.keys())
        keys.sort()

        self._liststore.clear()
        for x in keys:
            self._liststore.append(['%s' % (x)])

        unit = convert.dimension_default_unit[name]
        self.from_unit.set_active_id(unit)
        self.to_unit.set_active_id(unit)

    def _get_active_text(self, combobox):
        active = combobox.get_active()
        keys = list(self.units.keys())
        keys.sort()
        if active < 0:
            active = 0
        text = keys[active]
        if '<sup>' in text:
            text = text.split('<b>')[1].split('</b>')[0]
        return text

    def _convert(self, num_value, direction):
        if direction == 'from':
            unit = self._get_active_text(self.from_unit)
            to_unit = self._get_active_text(self.to_unit)
        elif direction == 'to':
            unit = self._get_active_text(self.to_unit)
            to_unit = self._get_active_text(self.from_unit)
        return convert.convert(num_value, unit, to_unit, self.units)

    def _insert_text_cb(self, entry, text, length, position):
        for char in text:
            if char == "-" and \
               entry.get_text() is "" and len(text) == 1:
                return False
            elif not re.match('[0-9,.]', char):
                entry.emit_stop_by_name('insert-text')
                return True
        return False

    def write_file(self, file_path):
        direction = 'from'
        if self.arrow.get_text() == '←':
            direction = 'to'
        state = {
            'dimension': self.dimension,
            'from-unit': self.from_unit.get_active_id(),
            'from-value': self.from_value.get_text(),
            'to-unit': self.to_unit.get_active_id(),
            'to-value': self.to_value.get_text(),
            'direction': direction,
        }
        self.metadata['state'] = json.dumps(state)
        open(file_path, 'w').close()

    def read_file(self, file_path):
        if 'state' in self.metadata:
            state = json.loads(self.metadata['state'])
            self.dimensions[state['dimension']].set_active(True)

            self.to_unit.set_active_id(state['to-unit'])
            self.from_unit.set_active_id(state['from-unit'])

            if state['direction'] == 'to':
                self.to_value.set_text(state['to-value'])
                self.from_value.set_text(state['from-value'])
            else:
                self.from_value.set_text(state['from-value'])
                self.to_value.set_text(state['to-value'])

            self._update_conversion(state['direction'])
