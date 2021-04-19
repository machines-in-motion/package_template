/**
 * @file demo_pid_load_from_file.cpp
 * @author Vincent Berenz
 * license License BSD-3-Clause
 * @copyright Copyright (c) 2019, New York University and Max Planck
 * Gesellschaft.
 * @date 2019-05-22
 *
 * @brief Example of a demo that requires to read a config file.
 * @see
 * https://git-amd.tuebingen.mpg.de/amd-clmc/package_template/wikis/catkin:-how-to-implement-a-demo
 *
 * @example demo_pid_load_from_file.cpp
 * Load the PID gains from a yaml file and create a PID controller from them.
 * This illustrates how to safely use the API when yaml file parsing is wanted.
 */

#include <stdexcept>
#include "package_template/file_configuration.hpp"
#include "package_template/pid.hpp"

/**
 * @brief Run some demo using a YAML file as configuration for the PID
 * controller.
 */
void run_demo()
{
    /* displaying what this demo is about */
    std::cout << "This demo shows how to create an executable run by the "
                 "continuous integration\n"
              << "which depends on a configuration file. In the solution "
                 "showed here, the absolute path\n"
              << "to the configuration file is set during pre-compilation. See "
                 "code in /demos/demo_pid_load_from_file.cpp\n"
              << "for details\n\n";

    /* reading gains (kp,kd,ki) from yaml config */

    // (look at the CMakeLists.txt to see why TEST_PID_GAINS_YAML_FILE_PATH is
    // replaced by correct abs path  during compilation)
    std::string config_file_path = TEST_PID_GAINS_YAML_FILE_PATH;

    // Gains_configuration is the base class for all configuration, including
    // the one read from yaml file, as done here.
    package_template::File_configuration gains =
        package_template::File_configuration(config_file_path);

    // printing to standard output the gains
    std::cout << "gains read from configuration file:" << std::endl;
    package_template::print_configuration(gains);

    // checking reading the config file when fine
    // if not, throwing corresponding error
    if (gains.has_error())
    {
        throw std::runtime_error(gains.get_error());
    }

    /* creating and running the controller */

    // PID controller creation
    package_template::PID controller(gains);

    // example of force computation
    double current_position = 1;
    double current_velocity = 1;
    double delta_time = 0.01;
    double target_position = 2;
    double force = controller.compute(
        current_position, current_velocity, target_position, delta_time);
    std::cout << "computed force: " << force << std::endl;

    // resetting integral of the controller
    controller.reset_integral();
}

/**
 * @brief Run the demo in a safe environment.
 */
int main()
{
    try
    {
        run_demo();
    }
    catch (const std::runtime_error& e)
    {
        std::cout << "demo failed !\nerror message:\n" << e.what() << std::endl;
        return 1;  // informs continuous integration that this demo did not run
                   // successfully
    }

    return 0;  // informs continuous integration that this demo did run
               // successfully
}
