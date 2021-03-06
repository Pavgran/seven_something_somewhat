# -*- coding: utf-8 -*-
import kivy
from kivy.uix import (
    layout
)
import kivy.uix.boxlayout as blayout
import numpy as np
from numpy import matlib as mtl
from kivy.lang import Builder
import kivy.uix.widget as widget
from kivy.uix import (
    relativelayout,
    floatlayout,
    label,
)
from kivy.properties import (
    ListProperty,
    ObjectProperty,
    NumericProperty,
    BooleanProperty,
)
import os
from kivy.factory import Factory
from kivy.uix.slider import Slider
from kivy.graphics import Mesh, Color, Translate
from math import cos, sin, pi, sqrt, degrees, radians
from kivy.uix.image import Image
import random as rnd
from kivy.uix.filechooser import *
from kivy.uix.popup import Popup
__author__ = 'ecialo'
H_COEF = sqrt(3)/2
R2 = radians(60)

# Factory.register('LoadDialog', cls=LoadDialog)

Builder.load_file('./mlp/widgets/grid/gridwidget.kv')


# class LoadDialog(floatlayout.FloatLayout):
#     load = ObjectProperty(None)
#     cancel = ObjectProperty(None)


def in_polygon(x, y, xp, yp):
    c = 0
    for i in range(len(xp)):
        if (((yp[i] <= y < yp[i-1]) or (yp[i-1] <= y < yp[i])) and
           (x > (xp[i-1] - xp[i]) * (y - yp[i]) / (yp[i-1] - yp[i]) + xp[i])):
                c = 1 - c
    return bool(c)


class HexCellWidget(relativelayout.FloatLayout):

    mesh_vertices = ListProperty([])
    circuit = ListProperty([])
    # mesh_texture = ObjectProperty(None)
    # hex_size = NumericProperty(40)
    is_selected = BooleanProperty(False)
    is_highlighted = BooleanProperty(False)
    rotator = mtl.eye(3)

    def __init__(self, cell, **kwargs):
        self.cell = cell
        # self.cell_pos = kwargs.pop('cell_pos')
        super(HexCellWidget, self).__init__(**kwargs)
        # self.update_vertices()
        # self.bind(rotator=self.update_vertices)

    def on_take(self, obj):
        self.remove_widget(obj.make_widget())

    def on_place(self, obj):
        self.add_widget(obj.make_widget())

    # def on_pos(self, _, __):
    #     if self.parent:
    #         self.update_vertices()

    @property
    def hex_size(self):
        return self.parent.cell_size

    def update_vertices(self):
        # print("UPDATE")
        vertices = []
        points = []
        # indices = []
        step = 6
        istep = (pi * 2) / float(step)
        # xx, yy = self.pos
        for i in range(step):
            x = cos(istep * i) * self.hex_size + self.hex_size
            y = sin(istep * i) * self.hex_size + self.hex_size*H_COEF

            c = np.matrix([[x], [y], [0]])
            m = (self.rotator * c)
            nx, ny = m[0, 0], m[1, 0]
            x, y = nx, ny
            # print(m.shape)

            vertices.extend([x, y, 0.5 + cos(istep * i)/2, 0.5 + sin(istep * i)/2])
            points.extend([x, y])
            # indices.append(i)
        # print id(self.mesh_vertices)
        self.circuit = points + points[0:2]
        # print(self, points)
        self.mesh_vertices = vertices
        # for child in self.children:
        #     try:
        #         child.update_verticies()
        #     except AttributeError:
        #         pass

    # def on_pos(self, _, __):
    #     for child in self.children:
    #         try:
    #             child.update_verticies()
    #         except AttributeError:
    #             pass

    @property
    def cell_pos(self):
        return self.cell.pos

    def on_touch_down(self, touch):
        ret = False
        touch.push()
        touch.apply_transform_2d(self.to_local)
        if self.collide_point(*touch.pos):
            self.parent.select_cell(self)
            ret = True
        touch.pop()
        return ret

    def collide_point(self, x, y):
        xs = self.mesh_vertices[::4]
        ys = self.mesh_vertices[1::4]
        # print(x, y)
        # print(xs[0], ys[0])
        return in_polygon(x, y, xs, ys)

    def to_local(self, x, y, relative=True):
        return super().to_local(x, y, relative)


class Hexgrid(widget.Widget):

    cell_indices = range(6)
    cell_size = NumericProperty(40)
    rotation = NumericProperty(0)
    rotator = mtl.eye(3)

    def __init__(self, grid, **kwargs):
        # hexgrid = kwargs.pop('hexgrid')
        hexgrid = grid
        self.grid = grid
        super(Hexgrid, self).__init__(**kwargs)
        self.hexgrid = hexgrid
        w, h = len(hexgrid._grid), len(hexgrid._grid[0])
        self._grid = [
            [None for _ in range(h)] for _ in range(w)]
        self.make_cells()
        # for column in self._grid:
        #     for cell in column:
        #         self.add_widget(cell)
        # self.update_children()
        self.bind(rotation=self.change_rotator)
        # self.bind(cell_size=self.update_children)

    def make_cells(self):
        for cell in self.grid:
            pos = cell.pos
            terrain = cell.terrain
            x, y = pos
            w = cell.make_widget(pos=self.grid_to_window(pos))
            self._grid[x][y] = w
            self.add_widget(w)
            if terrain:
                t = terrain.make_widget(pos_hint={'center_x': 0.5, 'center_y': 0.5})
                w.add_widget(t)
                # t.update_vertices()
                if cell.object:
                    o = cell.object.make_widget(pos_hint={'center_x': 0.5, 'center_y': 0.5})
                    w.add_widget(o)
                for _, content in enumerate(cell.additional_content):
                    c = content.make_widget(pos_hint={'center_x': 0.5, 'center_y': 0.5})
                    w.add_widget(c)
            w.add_widget(label.Label(text=str(pos), pos_hint={'center_x': 0.5, 'center_y': 0.5}))

    def change_rotator(self, _, value):
        rad = radians(value)
        self.rotator = np.matrix([
            [1.0, 0.0, 0.0],
            [0.0, cos(rad), sin(rad)],
            [0.0, -sin(rad), cos(rad)]
        ])
        for child in self.children:
            child.rotator = self.rotator
            child.pos = self.grid_to_window(child.cell_pos)
            child.update_vertices()
        # self.slider = Slider(pos=(100, 100), )

    def on_pos(self, inst, value):
        # print(self, new_pos, ololo)
        # super().on_pos(new_pos, ololo)
        self.update_children()

    def update_children(self, _=None, __=None):
        for child in self.children:
            child.pos = self.grid_to_window(child.cell_pos)
            child.update_vertices()

    def grid_to_window(self, pos):
        sx, sy = self.pos
        size = self.cell_size
        col, row = pos
        # print(col, row, type(col), type(row))
        x = size * 3 / 2 * col
        y = size * sqrt(3) * (row - 0.5 * (col & 1))

        # print(x, y)
        x, y = sx+x, sy+y
        # print(x, y)
        c = np.matrix([[x], [y], [0]])
        # R2 = radians(45)
        m = (self.rotator * c)
        # print(m)
        nx, ny = m[0, 0], m[1, 0]
        x, y = float(nx), float(ny)


        # print(x, y)
        return x, y

    def select_cell(self, cell):
        self.parent.cursor.select(cell)


class FullImage(Image):
    pass


# class RotateGridWidget(widget.Widget):
#
#     def show_load_background(self):
#         content = LoadDialog(load=self.load_background, cancel=self.dismiss_popup)
#         self._popup = Popup(title="Load background", content=content,
#                             size_hint=(0.9, 0.9))
#         self._popup.open()
#
#     def show_load_model(self):
#         content = LoadDialog(load=self.load_model, cancel=self.dismiss_popup)
#         self._popup = Popup(title="Load model", content=content,
#                             size_hint=(0.9, 0.9))
#         self._popup.open()
#
#     def load_background(self, path, filename):
#         back_texture = os.path.join(path, filename[0])
#         try:
#             texture = CoreImage(back_texture).texture
#             self.ids.background.texture = texture
#         except:
#             pass
#         self._popup.dismiss()
#
#     def load_model(self, path, filename):
#         back_texture = os.path.join(path, filename[0])
#         try:
#             texture = CoreImage(back_texture).texture
#             self.ids.model.texture = texture
#         except:
#             pass
#         self._popup.dismiss()
#
#     def dismiss_popup(self):
#         self._popup.dismiss()


if __name__ == '__main__':
    # from core.desk.common_desks import hexgrid_desk as hgd
    # from client.tools import bind_widget
    from kivy.app import App
    from kivy.core.image import Image as CoreImage
    # texture = CoreImage('/home/ecialo/grass.png')

    class CellMock(object):

        def __init__(self, i, j, texture_, is_selected=False):
            self.i = i
            self.j = j
            # self.texture = texture_
            self.is_selected = is_selected

    # grid = [[CellMock(0, 0, texture)]]
    h, w = 10, 10
    grid = [[CellMock(i, j, i == 0 and j == 0) for j in range(h)] for i in range(w)]

    class TestApp(App):

        def build(self):
            # wid = widget.Widget()
            wid = RotateGridWidget()
            # return wid
            # desk = hgd.HexgridDesk((20, 20))
            # desk_widget = desk.make_widget()
            # cell = HexCellWidget(texture=texture, pos=(300, 300))
            # background = FullImage(source='./grass.png', pos_hint={'x': 0.6, 'y': 0.6})
            grid_ = Hexgrid(hexgrid=grid, pos_hint={'x': 0.0, 'y': 0.0})
            wid.ids.rotator_sl.bind(value=lambda w, v: setattr(grid_, "rotation", v))
            wid.ids.c_size.bind(value=lambda w, v: setattr(grid_, 'cell_size', v))
            # wid.add_widget(background)
            wid.ids.grid.add_widget(grid_)
            return wid
            # return desk_widget

    TestApp().run()
