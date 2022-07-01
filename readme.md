# Filament Autoloader

## Install via Moonraker
Clone the repository into the home directory

    cd ~
    git clone https://github.com/eamars/filament-auto-loader.git

Then put the below block into the moonraker.conf

    [update_manager client z_calibration]
    type: git_repo
    path: ~/filament-auto-loader
    origin: https://github.com/eamars/filament-auto-loader.git
    install_script: install.sh
    managed_services: klipper

## Configuration

    [filament_autoloader autoloader]
    # The secondary extruder (known as the feeder)
    feeder_extruder: extruder_stepper secondary_extruder

    # The primary extruder for the direct drive setup
    toolhead_extruder: extruder

    # The toolhead sensor (the same ERCF uses)
    toolhead_sensor: filament_switch_sensor toolhead_sensor

    # The distance to retract when unloading
    unload_distance: 500

    # The distance to load before reaching the toolhead extruder. Default to 0
    # for safety reason
    load_prime_distance: 0

    # The distance to load between the toolhead sensor to the hotend
    filament_sensor_to_hotend_distance = 7.5
