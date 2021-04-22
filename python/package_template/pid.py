#!/usr/bin/env python

""" Brief description of the pid module.

    More advanced description of this module, e.g.
    This module contains a 1D PID controller and utilities for managing the
    gains and the controller parameters.

    Copyright (c) 2017-2019, New York University and Max Planck Gesellschaft,
    License BSD-3-Clause
"""


# Python 3 compatibility, has to be called just after the hashbang.
from __future__ import print_function, division
from pathlib import Path


class DefaultConfiguration(object):
    """PID configuration

    Configuration object with default values for kp, kd and ki
    can be used as input argument to create an instance of PID

    Attributes:
        kp: Proportional gain.
        kd: Derivative gain.
        ki: Integral gain.
    """

    kp = 1
    kd = 1
    ki = 1

    def __init__(self):
        self.kp = 1
        self.kd = 1
        self.ki = 1

    def __repr__(self):
        return "%s(kp=%r, kd=%r, ki=%r)" % (
            self.__class__.__name__,
            self.kp,
            self.kd,
            self.ki,
        )


class RosConfiguration:
    """ROS param configuration

    This contains the name of the ros parameter server keys for the PID gains.

    Attributes:
        ROSPARAM_KP: Key for reading kp gain.
        ROSPARAM_KD: Key for reading kd gain.
        ROSPARAM_KI: Key for reading ki gain.
    """

    ROSPARAM_KP = "kp"
    ROSPARAM_KD = "kd"
    ROSPARAM_KI = "ki"


class ConfigFileConfiguration:
    """  Path to default configuration file, relative to the pid package """

    ## Relative path to the default configuration fole
    relative_path = str(Path("config") / "test_pid_gains.yaml")


# "PythonPID" : to differentiate with cpp bindings PID
# see /srcpy/wrappers.cpp
class PythonPID:
    """
    Simple 1D PID controller

    Attributes:
        _configuration: The PID gains.
        _integral: The integral term.
    """

    def __init__(self, configuration):
        """Constructor, initiallize the PID gains from a given configuration.
        Args:
            configuration: Any object with "kp", "kd" and "ki" attributes
                           (as float)
        """
        self._configuration = configuration
        self._integral = 0

    def get_gains(self):
        """Get the gains in a dictionary, keys: "kp", "kd" and "ki"
        Returns:
            Dict `--` The PID gains.
        """
        return {
            "kp": self._configuration.kp,
            "kd": self._configuration.kp,
            "ki": self._configuration.ki,
        }

    def reset_integral(self):
        """ Reset integral part of the PID to 0.0 """
        self._integral = 0.0

    def compute(self, position, velocity, position_target, delta_time):
        """Compute the force related to the pid controller.

        This function is not stateless, as it performs integration.
        Call reset_integral() to reset the integral part.

        Args:
            position: Float `--` current position
            velocity: Float `--` current velocity
            position_target: Float `--` target position
            delta_time: Float `--` time passed since last measurement.
                                    Used for integral computation
        Returns:
            Float `--` computed force
        """
        position_error = position_target - position
        self._integral += delta_time * position_error
        return (
            position_error * self._configuration.kp
            - velocity * self._configuration.kd
            + self._integral * self._configuration.ki
        )

    def __str__(self):
        """  Convert the object into a string """
        return (
            "PID controller: kp:"
            + str(self._configuration.kp)
            + " kd:"
            + str(self._configuration.kd)
            + " ki:"
            + str(self._configuration.ki)
        )


def _read_yaml_config_file(file_path):
    """Parse a yaml file to get the PID gains.

    Convenience function for reading pid configuration from yaml file.

    Args:
        file_path: str `--` Path relative to the execution path or global path.
    """

    # importing yaml and reading yaml file
    import yaml

    assert Path(file_path).is_file()
    with open(file_path, "r") as f:
        yaml_load_object = yaml.load(f, Loader=yaml.Loader)

    # checking the yaml file had the excepted entries
    expected_attributes = ["kp", "kd", "ki"]
    if isinstance(yaml_load_object, DefaultConfiguration):
        for attribute in expected_attributes:
            if not hasattr(yaml_load_object, attribute):
                raise Exception(
                    "Configuration file "
                    + str(file_path)
                    + " is expected to have the "
                    + str(attribute)
                    + " entry"
                )
        Config = yaml_load_object
    elif isinstance(yaml_load_object, dict):
        for attribute in expected_attributes:
            if not attribute in yaml_load_object.keys():
                raise Exception(
                    "Configuration file "
                    + str(file_path)
                    + " is expected to have the "
                    + str(attribute)
                    + " entry"
                )
        # creating a config object with correct attributes
        class Config(object):
            pass

        for attribute in expected_attributes:
            try:
                setattr(Config, attribute, float(yaml_load_object[attribute]))
            except Exception:
                raise Exception(
                    "failed to convert "
                    + attribute
                    + "("
                    + str(yaml_load_object[attribute])
                    + ") to float (file: "
                    + str(file_path)
                    + ")"
                )

    # constructing and returning controller
    return PythonPID(Config)


def get_default_pid():
    """Factory for default PID controller.

    See PID and see DefaultConfiguration.

    Returns:
        PID `--` a new PID controller based on the DefaultConfiguration.
    """
    return PythonPID(DefaultConfiguration)


def get_ros1_params_pid(verbose=True):
    """Get a PID controller parameterized through ROS params

    Assumes roscore is running and suitable parameters have been written in the
    server.

    Args:
        verbose:  Bool `--` True: prints (stdout) the ros parameters it reads.

    Returns:
        PID `--` A PID object based on gains read from the ROS parameter server.
    """
    # importing ros and checking roscore is running
    import rospy

    if rospy.is_shutdown():
        raise Exception("failed to read ros parameters: ros is shutdown")
    # placeholder for the config
    class config:
        kp = None
        kd = None
        ki = None

    # reading the gains from ros parameter server
    parameters = [
        RosConfiguration.ROSPARAM_KP,
        RosConfiguration.ROSPARAM_KD,
        RosConfiguration.ROSPARAM_KI,
    ]
    gains = ["kp", "kd", "ki"]
    # if requested, printing the parameters it is about to read
    if verbose:
        print("reading ros parameters: " + ", ".join(parameters))
    for parameter, gain in zip(parameters, gains):
        if not rospy.has_param(parameter):
            raise Exception(
                "ros parameter server does not have the requested parameter: "
                + str(parameter)
                + " (current parameters: "
                + ", ".join(rospy.get_param_names())
                + ")"
            )
        try:
            value = rospy.get_param(parameter)
            setattr(config, gain, value)
        except Exception as e:
            raise Exception(
                "failed to read ros parameter "
                + str(parameter)
                + ": "
                + str(e)
            )
    # constructing and returning controller
    return PythonPID(config)


def get_config_file_pid(config_file_path=None, verbose=True):
    """Reads a yaml file and return a corresponding PID controller.

    Args:
        config_file_path: str `--` Path to configuration file relative to the
                          script where this function is defined is specified in
                          the ConfigFileConfiguration object. If None, uses
                          default config file (in config folder), else used
                          specified path
        verbose: Bool `--` If True, prints path to config file used to standard output

    Returns:
        PID `--` A PID based on gains read from default configuration file
    """
    if config_file_path is None:
        # getting abs path to this script
        abs_path_config = str(
            Path(__file__).resolve().parent.parent.parent
            / ConfigFileConfiguration.relative_path
        )
    else:
        abs_path_config = config_file_path
    # checking file exists
    if not Path(abs_path_config).is_file():
        raise Exception(
            "failed to find configuration file: " + str(abs_path_config)
        )
    # printing path to config file if asked
    if verbose:
        print("reading pid gains from: ", abs_path_config)
    # constructing and returning the controller
    return _read_yaml_config_file(abs_path_config)
