import bpy
from bgl import *
import mathutils


# These constants are missing from Blender OpenGL Wrapper
GL_LINK_STATUS = 35714
GL_VALIDATE_STATUS = 35715


def print_shader_errors(shader, task, code):
    """Print shader compilation errors to console.
    shader (int): The compiled shader object.
    task (string): The task which failed shader compilation.
    This is an helper string to be displayed in console.
    code (string): The shader source code.
    """
    log = Buffer(GL_BYTE, [5000])
    length = Buffer(GL_INT, 1)
    glGetShaderInfoLog(shader, len(log), length, log)
    
    print("GLSL Shader: %s error:" % task)
    for line, content in enumerate(code.splitlines()):
        print("%d %s" % (line+1, content))
    print()
    print(bytes(log[:length[0]]).decode())

def load_shader(type, filename):
    shader = glCreateShader(type)
    success = Buffer(GL_INT, 1)
    
    shadersource = bpy.data.texts[filename].as_string()
    glShaderSource(shader, shadersource)
    
    glCompileShader(shader)
    
    glGetShaderiv(shader, GL_COMPILE_STATUS, success)
    if success[0] == GL_FALSE:
        print_shader_errors(shader, 'compile', shadersource)
        return
    
    return shader

def init_shader():
    global vertex_shader
    global fragment_shader
    global program
    
    success = Buffer(GL_INT, 1)
    
    vertex_shader = load_shader(GL_VERTEX_SHADER, 'terrain.vert')
    fragment_shader = load_shader(GL_FRAGMENT_SHADER, 'terrain.frag')
    
    if not vertex_shader or not fragment_shader:
        return
    
    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    
    glLinkProgram(program)
    glGetProgramiv(program, GL_LINK_STATUS, success)
    if success[0] == GL_FALSE:
        print_shader_errors(fragment_shader, 'link', shadersource)
        return
    
    glValidateProgram(program)
    glGetProgramiv(program, GL_VALIDATE_STATUS, success)
    if success[0] == GL_FALSE:
        print_shader_errors(fragment_shader, 'validate', shadersource)
        return

def free_shader():
    if program: glDeleteProgram(program)
    if fragment_shader: glDeleteShader(fragment_shader)
    if vertex_shader: glDeleteShader(vertex_shader)

def draw_callback_px(self, context):
    glEnable(GL_BLEND)
    glColor4f(1.0, 0.0, 0.0, 0.5)

    glPushMatrix() # GL_MODELVIEW
    
    viewport = context.region_data
    
    modelview_matrix = viewport.view_matrix
    modelview_matrix = [modelview_matrix[j][i] if abs(modelview_matrix[j][i]) > 0.00001 else 0 for i in range(4) for j in range(4)]
    modelview_buffer = Buffer(GL_FLOAT, 16, modelview_matrix)
    glLoadMatrixf(modelview_buffer)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    projection_matrix = viewport.perspective_matrix * viewport.view_matrix.inverted()
    projection_matrix = [projection_matrix[j][i] if abs(projection_matrix[j][i]) > 0.00001 else 0 for i in range(4) for j in range(4)]
    projection_buffer = Buffer(GL_FLOAT, 16, projection_matrix)
    glLoadMatrixf(projection_buffer)

    glUseProgram(program)
    
    # vec3 unf7 type6 mat4_world_to_cam * (-vec3_lamp_Z_axis)
    sun = bpy.data.objects[bpy.data.lamps[0].name]
    sun_ray = viewport.view_matrix * sun.matrix_world * mathutils.Vector((0, 0, -1)) - viewport.view_matrix * sun.location
    
    uniform_loc = glGetUniformLocation(program, 'unf7')
    light_direction = Buffer(GL_FLOAT, 3, sun_ray.normalized())
    glUniform3fv(uniform_loc, 1, light_direction);
    
    # vec4 unf19 type11 GPU_DYNAMIC_LAMP_DYNCOL => diffuse
    uniform_loc = glGetUniformLocation(program, 'unf19')
    light_diffuse = Buffer(GL_FLOAT, 4, (1.0, 1.0, 1.0, 1.0))
    glUniform4fv(uniform_loc, 1, light_diffuse)
    
    # vec3 unf44; type 11 GPU_DYNAMIC_LAMP_DYNCOL => specular
    uniform_loc = glGetUniformLocation(program, 'unf44')
    light_specular = Buffer(GL_FLOAT, 3, (1.0, 1.0, 1.0))
    glUniform3fv(uniform_loc, 1, light_specular)

    glBegin(GL_QUADS)
    glVertex3f(-1.0, -1.0, 0.0)
    glVertex3f(1.0, -1.0, 0.0)
    glVertex3f(1.0, 1.0, 0.0)
    glVertex3f(-1.0, 1.0, 0.0)
    glEnd()
    
    glUseProgram(0)
    
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

    # restore opengl defaults
    glDisable(GL_BLEND)
    glColor4f(0.0, 0.0, 0.0, 1.0)


class ModalDrawOperator(bpy.types.Operator):
    """Draw a tessellated quad"""
    bl_idname = "view3d.modal_operator"
    bl_label = "Tessellation Operator"

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'LEFTMOUSE':
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            free_shader()
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            free_shader()
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            init_shader()
            # the arguments we pass the the callback
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def register():
    bpy.utils.register_class(ModalDrawOperator)


def unregister():
    bpy.utils.unregister_class(ModalDrawOperator)

if __name__ == "__main__":
    register()

