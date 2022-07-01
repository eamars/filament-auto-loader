import logging


class FilamentAutoLoader(object):
    def __init__(self, config):
        self.config = config
        self.printer = config.get_printer()

        self.feeder_extruder_name = config.get('feeder_extruder')
        self.toolhead_extruder_name = config.get('toolhead_extruder')
        self.toolhead_sensor_name = config.get('toolhead_sensor')

        self.unload_distance = config.getfloat('unload_distance', 500)
        self.load_prime_distance = config.getfloat('load_prime_distance', 0)
        self.filament_sensor_to_hotend_distance = config.getfloat('filament_sensor_to_hotend_distance', 0)

        self.long_move_distance = config.getfloat('long_move_distance', 50)
        self.long_move_speed = config.getfloat('long_move_speed', 100.)
        self.long_move_accel = config.getfloat('long_move_accel', 400.)

        self.short_move_distance = config.getfloat('short_move_distance', 1)
        self.short_move_speed = config.getfloat('short_move_speed', 25.)
        self.short_move_accel = config.getfloat('short_move_accel', 400.)

        self.gcode = self.printer.lookup_object('gcode')
        self.gcode.register_command('FILAMENT_AUTO_LOADER_LOAD',
                                    self.cmd_FILAMENT_AUTO_LOADER_LOAD,
                                    desc='Load the filament to the toolhead')
        self.gcode.register_command('FILAMENT_AUTO_LOADER_UNLOAD',
                                    self.cmd_FILAMENT_AUTO_LOADER_UNLOAD,
                                    desc='Unload the filament from the toolhead')

        self.printer.register_event_handler('klippy:connect', self.handle_connect)

    def handle_connect(self):
        self.feeder_extruder = self.printer.lookup_object(self.feeder_extruder_name)
        self.toolhead_extruder = self.printer.lookup_object(self.toolhead_extruder_name)
        self.toolhead_sensor = self.printer.lookup_object(self.toolhead_sensor_name)
        self.toolhead = self.printer.lookup_object('toolhead')

    def _extruder_move(self, target_move_distance, move_speed, wait=True, log_handler=None):
        if log_handler is None:
            log_handler = lambda x: None

        if target_move_distance >= 0:
            direction = 1
        else:
            direction = -1

        # Reset current E position
        self.gcode.run_script_from_command('G92 E0')

        # Get initial position
        # Position includes [x, y, z, e]
        position = self.toolhead.get_position()

        accumulated_move_distance = 0

        move_distance = self.long_move_distance * direction

        while abs(target_move_distance - accumulated_move_distance) >= abs(move_distance):
            position[3] += move_distance
            accumulated_move_distance += move_distance
            self.toolhead.move(position, move_speed)
            log_handler('Current: {}, Target: {}'.format(accumulated_move_distance, target_move_distance))
            if wait:
                self.toolhead.wait_moves()

        # Now the remaining distance (if any) is less than the long move distance then we shall move the remaining
        # distance using the short distance move
        remain_distance = target_move_distance - accumulated_move_distance
        if remain_distance > 0:
            position[3] += remain_distance
            accumulated_move_distance += remain_distance
            self.toolhead.move(position, move_speed)
            log_handler('Current: {}, Target: {}'.format(accumulated_move_distance, target_move_distance))
            if wait:
                self.toolhead.wait_moves()

        return accumulated_move_distance

    def cmd_FILAMENT_AUTO_LOADER_LOAD(self, gcmd):
        log_handler = lambda x: gcmd.respond_info(x)
        log_handler('Start Loading')

        self.gcode.run_script_from_command('G92 E0')
        accumulated_move_distance = 0

        # Load to the prime distance
        accumulated_move_distance += self._extruder_move(self.load_prime_distance, move_speed=self.long_move_speed,
                                                         wait=False, log_handler=log_handler)
        self.toolhead.wait_moves()

        # Load until the filament sensor is triggered
        while not bool(self.toolhead_sensor.runout_helper.filament_present):
            accumulated_move_distance += self._extruder_move(self.short_move_distance, move_speed=self.short_move_speed,
                                                             wait=True, log_handler=log_handler)

        # Load to the hotend
        accumulated_move_distance += self._extruder_move(self.filament_sensor_to_hotend_distance,
                                                         move_speed=self.short_move_speed,
                                                         wait=True,
                                                         log_handler=log_handler)

        log_handler('Load Complete. Total Extrusion Distance: {}'.format(accumulated_move_distance))

    def cmd_FILAMENT_AUTO_LOADER_UNLOAD(self, gcmd):
        gcmd.respond_info('Start Unloading')

        self._extruder_move(-self.unload_distance, move_speed=self.long_move_speed,
                            wait=False, log_handler=lambda x: gcmd.respond_info(x))
        self.toolhead.wait_moves()
        gcmd.respond_info('Unload Complete')


def load_config_prefix(config):
    return FilamentAutoLoader(config)
