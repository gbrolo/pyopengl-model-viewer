import glm
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

        glClearColor(0.0, 0.0, 0.0, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

    def load_shaders(self):
        self.vertex_shader = open('shaders/vertex_shader.shader', 'r').read()
        self.fragment_shader = open('shaders/fragment_shader.shader', 'r').read()

        self.active_shader = shaders.compileProgram(
            shaders.compileShader(self.vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(self.fragment_shader, GL_FRAGMENT_SHADER),
        )

        glUseProgram(self.active_shader)

    def load_matrixes(self):
        self.model_matrix = glm.mat4(1)
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
        self.camera = glm.vec3(0, 0, 200)
        self.camera_speed = 50

    def gl_apply(self, node, directory_path='./models/spider/'):
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
            glGetUniformLocation(self.active_shader, "model"), 
            1,
            GL_FALSE, 
            glm.value_ptr(self.model_matrix)
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "view"), 
            1,
            GL_FALSE, 
            glm.value_ptr(self.view_matrix)
        )

        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "projection"), 
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
            glGetUniformLocation(self.active_shader, "light"), 
            -100, 
            300, 
            0, 
            1
        )

    def viewer_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                return False   
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.camera.x += self.camera_speed
                    self.camera.z += self.camera_speed
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.camera.x -= self.camera_speed
                    self.camera.z -= self.camera_speed
        return True    

if __name__=='__main__':
    viewer = Viewer()
    viewer.set_viewport_size()
    viewer.pygame_init()
    viewer.load_shaders()
    viewer.load_matrixes()
    viewer.load_object('./models/spider/spider.obj')
    viewer.load_camera()    

    render = True

    while render:
        glClear(
            GL_COLOR_BUFFER_BIT |
            GL_DEPTH_BUFFER_BIT
        )

        current_view = glm.lookAt(
            viewer.camera,
            glm.vec3(0, 0, 0),
            glm.vec3(0, 1, 0)
        )

        viewer.gl_apply(
            viewer.obj.rootnode
        )

        render = viewer.viewer_input()
        viewer.clock.tick(15)
        pygame.display.flip()

