from bge import logic
import mathutils

EPSILON = 1.0e-10

align_damping = 5
align_filter = align_damping / (1.0 + align_damping)

def fakie(controller):
    snowboarder = controller.owner
    snowboarder['fakie'] = snowboarder.localLinearVelocity.y > 0

def align(controller):
    snowboarder = controller.owner
    orimat = snowboarder.worldOrientation
    z = orimat.col[2]
    object, hitpoint, normal = snowboarder.rayCast(snowboarder.worldPosition - z, None, 1, 'ground', 1)

    if normal:
        normal = align_filter * z + (1.0 - align_filter) * normal
        
        ori = orimat.col[1]
        if abs(normal.dot(ori)) > 1 - 3 * EPSILON:
            ori = orimat.col[0]

        xalign = ori.cross(normal)

        y = normal.cross(xalign)
        x = y.cross((0, 0, 1))
        z = x.cross(y)

        x.normalize()
        y.normalize()
        z.normalize()
        
        orimat.col[0] = x
        orimat.col[1] = y
        orimat.col[2] = z