# python/example4.py -- Python version of an example application that
# shows how to use the GLCanvas widget. For a C++ implementation, see
# '../src/example4.cpp'.
#
# NanoGUI was developed by Wenzel Jakob <wenzel@inf.ethz.ch>.
# The widget drawing code is based on the NanoVG demo application
# by Mikko Mononen.
#
# All rights reserved. Use of this source code is governed by a
# BSD-style license that can be found in the LICENSE.txt file.

import nanogui
import random
import math
import time
import gc

from nanogui import Color, Screen, Window, GroupLayout, BoxLayout, \
                    ToolButton, Label, Button, Widget, \
                    PopupButton, CheckBox, MessageDialog, VScrollPanel, \
                    ImagePanel, ImageView, ComboBox, ProgressBar, Slider, \
                    TextBox, ColorWheel, Graph, GridLayout, \
                    Alignment, Orientation, TabWidget, IntBox, GLShader, GLCanvas

from nanogui import gl, glfw, entypo


class MyGLCanvas(GLCanvas):
    def __init__(self, parent):
        super(MyGLCanvas, self).__init__(parent)

        try:
            import numpy as np

            self.shader = GLShader()
            if nanogui.opengl:
                self.shader.init(
                    # An identifying name
                    "a_simple_shader",

                    # Vertex shader
                    """#version 330
                    uniform mat4 model_view_proj;
                    in vec3 position;
                    in vec3 color;
                    out vec4 frag_color;
                    void main() {
                        frag_color = vec4(color, 1.0);
                        gl_Position = model_view_proj * vec4(position, 1.0);
                    }""",

                    # Fragment shader
                    """#version 330
                    out vec4 color;
                    in vec4 frag_color;
                    void main() {
                        color = frag_color;
                    }"""
                )
            else: # GLES 2
                self.shader.init(
                    # An identifying name
                    "a_simple_shader",

                    # Vertex shader
                    """precision highp float;
                    uniform mat4 model_view_proj;
                    attribute vec3 position;
                    attribute vec3 color;
                    varying vec4 frag_color;
                    void main() {
                        frag_color = vec4(color, 1.0);
                        gl_Position = model_view_proj * vec4(position, 1.0);
                    }""",

                    # Fragment shader
                    """precision highp float;
                    varying vec4 frag_color;
                    void main() {
                        gl_FragColor = frag_color;
                    }"""
                )

            # Draw a cube
            indices = np.array(
                [[0, 3, 3, 6, 7, 5, 4, 1, 4, 3, 5, 2],
                 [1, 2, 2, 7, 6, 4, 5, 0, 0, 7, 6, 1],
                 [3, 1, 6, 3, 5, 7, 1, 4, 3, 4, 2, 5]],
                dtype=np.int32)

            positions = np.array(
                [[-1, -1, 1, 1, -1, -1, 1, 1],
                 [1, 1, 1, 1, -1, -1, -1, -1],
                 [1, -1, -1, 1, 1, -1, -1, 1]],
                dtype=np.float32)

            colors = np.array(
                [[1, 0, 1, 0, 1, 0, 0.5, 1],
                 [0, 1, 1, 0, 0, 1, 0.5, 0],
                 [0, 0, 0, 1, 1, 1, 0.5, 0.5]],
                dtype=np.float32)

            self.shader.bind()
            self.shader.upload_indices(indices)
            self.shader.upload_attrib("position", positions)
            self.shader.upload_attrib("color", colors)
        except ImportError:
            self.shader = None
            pass

    def draw_gl(self):
        if self.shader is not None:
            import numpy as np
            self.shader.bind()

            current_time = time.time()
            angle_x = self.rotation[0] * current_time
            angle_y = self.rotation[1] * current_time
            angle_z = self.rotation[2] * current_time

            mvp_rot_x = np.matrix(
                [[1, 0, 0, 0],
                 [0, np.cos(angle_x), -np.sin(angle_x), 0],
                 [0, np.sin(angle_x), np.cos(angle_x), 0],
                 [0, 0, 0, 1]],
                dtype=np.float32)

            mvp_rot_y = np.matrix(
                [[np.cos(angle_y), 0, np.sin(angle_y), 0],
                 [0, 1, 0, 0],
                 [-np.sin(angle_y), 0, np.cos(angle_y), 0],
                 [0, 0, 0, 1]],
                dtype=np.float32)

            mvp_rot_z = np.matrix(
                [[np.cos(angle_z), -np.sin(angle_z), 0, 0],
                 [np.sin(angle_z), np.cos(angle_z), 0, 0],
                 [0, 0, 1, 0],
                 [0, 0, 0, 1]],
                dtype=np.float32)

            mvp = mvp_rot_x * mvp_rot_y * mvp_rot_z

            mvp[0:3, 0:3] *= 0.25

            self.shader.set_uniform("model_view_proj", mvp)

            gl.Enable(gl.DEPTH_TEST)
            self.shader.draw_indexed(gl.TRIANGLES, 0, 12)
            gl.Disable(gl.DEPTH_TEST)


class TestApp(Screen):
    def __init__(self):
        super(TestApp, self).__init__((800, 600), "NanoGUI Test", False)

        window = Window(self, "GLCanvas Demo")
        window.set_position((15, 15))
        window.set_layout(GroupLayout())

        self.canvas = MyGLCanvas(window)
        self.canvas.set_background_color(Color(0.5, 0.5, 0.5, 1.0))
        self.canvas.set_size((400, 400))

        self.canvas.rotation = [0.25, 0.5, 0.33]

        tools = Widget(window)
        tools.set_layout(BoxLayout(Orientation.Horizontal,
                                  Alignment.Middle, 0, 5))

        b0 = Button(tools, "Random Color")
        def cb0():
            self.canvas.set_background_color(Color(random.random(), random.random(), random.random(), 1.0))
        b0.set_callback(cb0)

        b1 = Button(tools, "Random Rotation")
        def cb1():
            self.canvas.rotation = [random.random(), random.random(), random.random()]
        b1.set_callback(cb1)

        self.perform_layout()

    def keyboard_event(self, key, scancode, action, modifiers):
        if super(TestApp, self).keyboard_event(key, scancode,
                                              action, modifiers):
            return True
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            self.set_visible(False)
            return True
        return False

if __name__ == "__main__":
    nanogui.init()
    test = TestApp()
    test.draw_all()
    test.set_visible(True)
    nanogui.mainloop()
    del test
    gc.collect()
    nanogui.shutdown()
