from bge import logic
import mathutils

EPSILON = 1.0e-10

#Air properties
air_raydist = 1.5
air_aligndamping = 50

# Ground properties
ground_raydist = 0.15
ground_aligndamping = 5
ground_tiltdamping = 10
ground_maxtilt = 0.4 # in range [0..1]

# Air constants
air_alignfilter = air_aligndamping / (1.0 + air_aligndamping)

# Ground constants
ground_raydist_squared = ground_raydist * ground_raydist
ground_alignfilter = ground_aligndamping / (1.0 + ground_aligndamping)
ground_tiltfilter = ground_tiltdamping / (1.0 + ground_tiltdamping)

armature = logic.getCurrentScene().objects['Armature']
ground_normal = None

def update(controller):
    global ground_normal
    
    snowboarder = controller.owner
    
    snowboarder['fakie'] = snowboarder.localLinearVelocity.y > 0
    
    orimat = snowboarder.worldOrientation
    z = orimat.col[2]
    direction = snowboarder.worldPosition - z
    object, hitpoint, normal = snowboarder.rayCast(direction, None, air_raydist, 'ground', 1, 1)

    if hitpoint:
        ray = hitpoint - snowboarder.worldPosition
        snowboarder['onground'] = ray.length_squared < ground_raydist_squared
    else:
        snowboarder['onground'] = False
    
    if snowboarder['onground']:
        filter = ground_alignfilter
        snowboarder.localLinearVelocity.x = 0
    else:
        filter = air_alignfilter
    
    if normal:
        ground_normal = normal
    else:
        normal = ground_normal
    
    normal = filter * z + (1.0 - filter) * normal
        
    ori = orimat.col[1]
    if abs(normal.dot(ori)) > 1 - 3 * EPSILON:
        ori = orimat.col[0]

    xalign = ori.cross(normal)
    yalign = normal.cross(xalign)
    zalign = normal
    
    xalign.normalize()
    yalign.normalize()
    zalign.normalize()

    filter = ground_tiltfilter
    hdir = snowboarder['hdir']
    
    y = yalign
    if snowboarder['onground'] and hdir != 0 and not snowboarder['crouch']:
        tilt = (1.0 - ground_maxtilt) * hdir * xalign - ground_maxtilt * zalign
        z = filter * armature.worldOrientation.col[2] - (1.0 - filter) * tilt
        x = y.cross(z)
    else:
        x = filter * armature.worldOrientation.col[0] + (1.0 - filter) * y.cross((0, 0, 1))
        z = x.cross(y)

    x.normalize()
    y.normalize()
    z.normalize()
    
    orimat.col[0] = xalign
    orimat.col[1] = yalign
    orimat.col[2] = zalign
    
    armaori = mathutils.Matrix([[x.x, y.x, z.x],
                                [x.y, y.y, z.y],
                                [x.z, y.z, z.z]])
    armature.localOrientation = orimat.inverted() * armaori