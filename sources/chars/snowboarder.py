from bge import logic
import mathutils

EPSILON = 1.0e-10

#Air properties
air_raydist = 2
air_aligndamping = 50

# Ground properties
ground_raydist = 0.15
ground_aligndamping = 5

# Air constants
air_alignfilter = air_aligndamping / (1.0 + air_aligndamping)

# Ground constants
ground_alignfilter = ground_aligndamping / (1.0 + ground_aligndamping)
ground_raydist_squared = ground_raydist * ground_raydist

def update(controller):
    snowboarder = controller.owner
    
    snowboarder['fakie'] = snowboarder.localLinearVelocity.y > 0
    
    orimat = snowboarder.worldOrientation
    z = orimat.col[2]
    direction = snowboarder.worldPosition - z
    object, hitpoint, normal = snowboarder.rayCast(direction, None, air_raydist, 'ground', 1)

    if hitpoint:
        ray = hitpoint - snowboarder.worldPosition
        dist_squared = ray.length_squared
        
        if dist_squared < ground_raydist_squared:
            snowboarder['onground'] = True
            filter = ground_alignfilter
        else:
            snowboarder['onground'] = False
            filter = air_alignfilter
        
        normal = filter * z + (1.0 - filter) * normal
        
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
    else:
        snowboarder['onground'] = False