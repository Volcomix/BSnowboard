import bpy
import bge
from bge import logic
from bgl import *

# Missing constant in Blender OpenGL Wrapper
GL_CLAMP_TO_EDGE = 33071
GL_LINK_STATUS = 35714
GL_VALIDATE_STATUS = 35715

viewport = None
texname = None
shader = None
program = None
camera = None
viewprojectionmatrix = None
parameters = None

def init_viewport():
    global viewport
    viewport = [bpy.context.region.x,
                bpy.context.region.y,
                bge.render.getWindowWidth() + 1,
                bge.render.getWindowHeight() + 1]

def init_camera(controller):
    global camera
    global viewprojectionmatrix
    
    camera = controller.owner
    viewprojectionmatrix = camera.projection_matrix * camera.world_to_camera

def init_textures():
    global texname
    texname = Buffer(GL_INT, 3, [-1, -1, -1])
    
    texturewidth = viewport[2]
    textureheight = viewport[3]
    teximage = [Buffer(GL_BYTE, [texturewidth * textureheight * 4])] * 2
    
    glGenTextures(2, texname)
    
    glBindTexture(GL_TEXTURE_2D, texname[0])
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, texturewidth, textureheight, 0, GL_RGBA, GL_UNSIGNED_BYTE, teximage[0])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    
    glBindTexture(GL_TEXTURE_2D, texname[1])
    glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, texturewidth, textureheight, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, teximage[1])
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_NONE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

def free_textures():
    glDeleteTextures(2, texname)

def print_shader_errors(shader, task, code):
    log = Buffer(GL_BYTE, [5000])
    length = Buffer(GL_INT, 1)
    glGetShaderInfoLog(shader, len(log), length, log)
    
    print("2D Filter GLSL Shader: %s error:" % task)
    for line, content in enumerate(code.splitlines()):
        print("%d %s" % (line+1, content))
    print()
    print(bytes(log[:length[0]]).decode())

def init_shader(controller):
    global shader
    global program
    
    shader = glCreateShader(GL_FRAGMENT_SHADER)
    success = Buffer(GL_INT, 1)
    
    shadersource = controller.actuators['MotionBlur'].shaderText
    glShaderSource(shader, shadersource)
    
    glCompileShader(shader)
    
    glGetShaderiv(shader, GL_COMPILE_STATUS, success)
    if success[0] == GL_FALSE:
        print_shader_errors(shader, 'compile', shadersource)
        return
    
    program = glCreateProgram()
    glAttachShader(program, shader)
    
    glLinkProgram(program)
    glGetProgramiv(program, GL_LINK_STATUS, success)
    if success[0] == GL_FALSE:
        print_shader_errors(shader, 'link', shadersource)
        return
    
    glValidateProgram(program)
    glGetProgramiv(program, GL_VALIDATE_STATUS, success)
    if success[0] == GL_FALSE:
        print_shader_errors(shader, 'validate', shadersource)
        return

def free_shader():
    glDeleteProgram(program)
    glDeleteShader(shader)

def draw_filter():
    global viewprojectionmatrix
    
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texname[0])
    glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, viewport[0], viewport[1], viewport[2], viewport[3], 0)
    
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, texname[1])
    glCopyTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, viewport[0], viewport[1], viewport[2], viewport[3], 0)
    
    # reverting to texunit 0, without this we get bug [#28462]
    glActiveTexture(GL_TEXTURE0)
    
    glDisable(GL_DEPTH_TEST)
    # in case the previous material was wire
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
    # if the last rendered face had alpha add it would messes with the color of the plane we apply 2DFilter to
    glDisable(GL_BLEND)
    # fix for [#34523] alpha buffer is now available for all OSs
    glDisable(GL_ALPHA_TEST)
    
    glPushMatrix() # GL_MODELVIEW
    glLoadIdentity() # GL_MODELVIEW
    glMatrixMode(GL_TEXTURE)
    glLoadIdentity()
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    glUseProgram(program)
    
    uniformLoc = glGetUniformLocation(program, 'sceneSampler')
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_2D, texname[0])
    glUniform1i(uniformLoc, 0)
    
    uniformLoc = glGetUniformLocation(program, 'depthTexture')
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, texname[1])
    glUniform1i(uniformLoc, 1)
    
    previousviewprojectionmatrix = viewprojectionmatrix
    viewprojectionmatrix = camera.projection_matrix * camera.world_to_camera
    viewprojectioninversematrix = viewprojectionmatrix.copy()
    viewprojectioninversematrix.invert()
    
    uniformLoc = glGetUniformLocation(program, 'viewProjectionInverseMatrix')
    viewprojectioninversematrix = Buffer(GL_FLOAT, [4, 4], viewprojectioninversematrix)
    glUniformMatrix4fv(uniformLoc, 1, GL_FALSE, viewprojectioninversematrix);
    
    uniformLoc = glGetUniformLocation(program, 'previousViewProjectionMatrix')
    previousviewprojectionmatrix = Buffer(GL_FLOAT, [4, 4], previousviewprojectionmatrix)
    glUniformMatrix4fv(uniformLoc, 1, GL_FALSE, previousviewprojectionmatrix);
    
    uniformLoc = glGetUniformLocation(program, 'numSamples')
    glUniform1f(uniformLoc, parameters['motionblur_numSamples'])
    
    uniformLoc = glGetUniformLocation(program, 'detail')
    glUniform1f(uniformLoc, parameters['motionblur_detail'])
    
    glBegin(GL_QUADS)
    
    glColor4f(1, 1, 1, 1)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(1,1)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(-1,1)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(-1,-1)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(1,-1)
    
    glEnd()

    glEnable(GL_DEPTH_TEST)
    glUseProgram(0);
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def init_filter(controller):
    global parameters
    parameters = controller.owner
    
    scene = logic.getCurrentScene()
    scene.post_draw.append(draw_filter)

def init(controller):
    init_viewport()
    init_camera(controller)
    init_textures()
    init_shader(controller)
    init_filter(controller)

def free():
    free_shader()
    free_textures()