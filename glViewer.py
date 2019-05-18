import glm
import math
import numpy
import pygame
import logging
import pyassimp
import OpenGL.GL.shaders as shaders

from OpenGL.GL import *

logger = logging.getLogger("pyassimp")
gllogger = logging.getLogger("OpenGL")
gllogger.setLevel(logging.WARNING)
logging.basicConfig(level=logging.INFO)

class Viewer:
    def set_viewport_size(self):
        self.viewport_width = 800
        self.viewport_height = 600

    def pygame_init(self):
        pygame.init()
        pygame.display.set_mode(
            (self.viewport_width, self.viewport_height),
            pygame.OPENGL | pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        pygame.key.set_repeat(1, 10)

        glClearColor(1.0, 1.0, 1.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

    def load_shaders(self):
        self.vertex_shader = open('shaders/vertex_shader.shader', 'r').read()        
        self.fragment_shader = open('shaders/fragment_shader.shader', 'r').read()

        self.active_shader = shaders.compileProgram(
            shaders.compileShader(self.vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(self.fragment_shader, GL_FRAGMENT_SHADER),
        )

        self.active_shader_info = 'NORMAL_VERTEX'

        glUseProgram(self.active_shader)

    def change_shader(self, shader):
        self.active_shader_info = shader  

        if shader == 'NIGHT_VERTEX':
            glClearColor(0.0, 0.0, 0.0, 0.0)
        else:
            glClearColor(1.0, 1.0, 1.0, 1.0)

    def load_matrixes(self):
        self.model = glm.mat4(1)
        self.view_matrix = glm.mat4(1)
        self.projection_matrix = glm.perspective(
            glm.radians(45),
            self.viewport_width / self.viewport_height,
            0.1,
            1000.0
        )

        glViewport(0, 0, self.viewport_width, self.viewport_height)

    def load_object(self, path):
        logger.info('Loading object: ' + path)
        self.obj = pyassimp.load(path)
        obj = self.obj
        logger.info("  meshes: %d" % len(obj.meshes))
        logger.info("  total faces: %d" % sum([len(mesh.faces) for mesh in obj.meshes]))
        logger.info("  materials: %d" % len(obj.materials))  

    def load_camera(self):
        self.camera = glm.vec3(14.283286094665527, 35.90460968017578, 158.73951721191406)
        self.camera_speed = 15
        self.angle = 340

    def gl_apply(self, node, directory_path='./models/hokage/'):
        self.model = node.transformation.astype(numpy.float32)

        for mesh in node.meshes:
            current_material = dict(mesh.material.properties.items())
            tex = current_material['file'][2:]
            tex_surface = pygame.image.load(directory_path + tex)

            tex_data = pygame.image.tostring(
                tex_surface,
                'RGB',
                1
            )
            
            tex_w = tex_surface.get_width()
            tex_h = tex_surface.get_height()

            tex = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, tex_w, tex_h, 0, GL_RGB, GL_UNSIGNED_BYTE, tex_data)
            glGenerateMipmap(GL_TEXTURE_2D)

            vertices = numpy.hstack((
                numpy.array(mesh.vertices, dtype = numpy.float32),
                numpy.array(mesh.normals, dtype = numpy.float32),
                numpy.array(mesh.texturecoords[0], dtype = numpy.float32)
            ))

            faces = numpy.hstack(
                numpy.array(mesh.faces, dtype = numpy.int32)
            )

            diffuse = mesh.material.properties["diffuse"]

            self.set_gl_bindings(vertices, faces)
            self.set_matrices_bindings(diffuse)

            glDrawElements(GL_TRIANGLES, len(faces), GL_UNSIGNED_INT, None)

        for child in node.children:
            self.gl_apply(child, directory_path)

    def set_gl_bindings(self, vertices, faces):
        # vertices
        vertex_buffer = glGenVertexArrays(1)
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, False, 36, None)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, False, 36, ctypes.c_void_p(12))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 3, GL_FLOAT, False, 36, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)

        # faces
        element_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, element_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces, GL_STATIC_DRAW)

    def set_matrices_bindings(self, diffuse):
        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "model_matrix"), 
            1,
            GL_FALSE, 
            self.model
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "view_matrix"), 
            1,
            GL_FALSE, 
            glm.value_ptr(self.view_matrix)
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "projection_matrix"), 
            1,
            GL_FALSE, 
            glm.value_ptr(self.projection_matrix)
        )

        glUniform4f(
            glGetUniformLocation(self.active_shader, "color"),
            *diffuse,
            1
        )

        glUniform4f(
            glGetUniformLocation(self.active_shader, "shader_light"), 
            200 if self.active_shader_info == 'INVERTED_SUN' else -50 if self.active_shader_info == 'NIGHT_VERTEX' else -200, 
            300, 
            0, 
            200 if self.active_shader_info == 'SUNNY_VERTEX' else -75 if self.active_shader_info == 'NIGHT_VERTEX' else 75
        )

    def print_camera(self):
        camera = (self.camera.x, self.camera.y, self.camera.z)
        print('Camera:', camera, 'Angle: ', self.angle)

    def viewer_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                return False   
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.angle += self.camera_speed
                    
                    x = self.camera.x + self.camera_speed * math.cos(math.radians(1/2 * self.angle))                    
                    self.camera.x = x

                    z = self.camera.z + self.camera_speed * math.sin(math.radians(1/2 * self.angle))                    
                    self.camera.z = z

                    self.print_camera()
                elif event.key == pygame.K_RIGHT:
                    self.angle += (-self.camera_speed)
                    
                    x = self.camera.x - self.camera_speed * math.cos(math.radians(1/2 * self.angle))                    
                    self.camera.x = x

                    z = self.camera.z - self.camera_speed * math.sin(math.radians(1/2 * self.angle))                    
                    self.camera.z = z

                    self.print_camera()
                elif event.key == pygame.K_UP:
                    if (-240.0 <= self.camera.z <= -90.0) or (90.0 <= self.camera.z <= 240.0):
                        y = self.camera.y + self.camera_speed * math.cos(math.radians(self.angle))

                        if (4.0 < y < 180.0):
                            self.camera.y = y

                        self.print_camera()
                elif event.key == pygame.K_DOWN:
                    if (-240.0 <= self.camera.z <= -90.0) or (90.0 <= self.camera.z <= 240.0):
                        y = self.camera.y - self.camera_speed * math.cos(math.radians(self.angle))

                        if (4.0 < y < 180.0):
                            self.camera.y = y

                        self.print_camera()
                elif event.key == pygame.K_s:
                    z = self.camera.z + self.camera_speed * math.cos(math.radians(self.angle))
                    if (-240.0 <= z <= -90.0) or (90.0 <= z <= 240.0):
                        self.camera.z = z

                    self.print_camera()
                elif event.key == pygame.K_w:
                    z = self.camera.z - self.camera_speed * math.cos(math.radians(self.angle))
                    if (-240.0 <= z <= -90.0) or (90.0 <= z <= 240.0):
                        self.camera.z = z

                    self.print_camera()
                elif event.key == pygame.K_1:
                    self.change_shader('NORMAL_VERTEX')
                elif event.key == pygame.K_2:
                    self.change_shader('SUNNY_VERTEX')
                elif event.key == pygame.K_3:
                    self.change_shader('NIGHT_VERTEX')
                elif event.key == pygame.K_4:
                    self.change_shader('INVERTED_SUN')
        return True    

if __name__=='__main__':
    viewer = Viewer()
    viewer.set_viewport_size()
    viewer.pygame_init()
    viewer.load_shaders()
    viewer.load_matrixes()
    viewer.load_object('./models/hokage/office_2.obj')
    viewer.load_camera()    

    render = True

    while render:
        glClear(
            GL_COLOR_BUFFER_BIT |
            GL_DEPTH_BUFFER_BIT
        )

        viewer.view_matrix = glm.lookAt(
            viewer.camera,
            glm.vec3(10, 10, 0),
            glm.vec3(0, 50, 0)
        )

        viewer.gl_apply(
            viewer.obj.rootnode,
            './models/hokage/'
        )

        render = viewer.viewer_input()
        viewer.clock.tick(30)
        pygame.display.flip()

