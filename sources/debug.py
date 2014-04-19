import bge
from bge import logic

def actions(controller):
    object = controller.owner

    status = ['{} {}'.format(sens.actuator[:-9], sens.status) for sens in controller.sensors if isinstance(sens, bge.types.SCA_ActuatorSensor)]
    state = [i + 1 for i in range(30) if (object.state & (1<<i)) == (1<<i)]
    print(status, state)