cmake_minimum_required(VERSION 3.10.2)
project(package_template VERSION 2.0.0)

# Using C++17
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

#
# Dependencies
#

find_package(yaml_utils REQUIRED)
find_package(mpi_cmake_modules REQUIRED)
find_package(pybind11 REQUIRED)

# prepare to export all needed targets
set(all_targets)

#
# Library
#

add_library(
  ${PROJECT_NAME} SHARED
  src/gains_configuration.cpp src/default_configuration.cpp
  src/file_configuration.cpp src/pid.cpp)
target_include_directories(
  ${PROJECT_NAME} PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
                         $<INSTALL_INTERFACE:include>)
target_link_libraries(${PROJECT_NAME} yaml_utils::yaml_utils)
list(APPEND all_targets ${PROJECT_NAME})

#
# Python wrappers
#

add_library(${PROJECT_NAME}_cpp_bindings MODULE srcpy/wrappers.cpp)
target_link_libraries(${PROJECT_NAME}_cpp_bindings PRIVATE pybind11::module)
target_link_libraries(${PROJECT_NAME}_cpp_bindings PRIVATE ${PYTHON_LIBRARIES})
target_link_libraries(${PROJECT_NAME}_cpp_bindings PRIVATE ${PROJECT_NAME})
set_target_properties(${PROJECT_NAME}_cpp_bindings
                      PROPERTIES PREFIX "" SUFFIX "${PYTHON_MODULE_EXTENSION}")
target_include_directories(
  ${PROJECT_NAME}_cpp_bindings
  PUBLIC $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
         $<INSTALL_INTERFACE:include>
  PUBLIC ${PYTHON_INCLUDE_DIRS})
get_python_install_dir(python_install_dir)
install(TARGETS ${PROJECT_NAME}_cpp_bindings DESTINATION ${python_install_dir})
list(APPEND all_targets ${PROJECT_NAME}_cpp_bindings)

#
# Unit tests
#
include(CTest)
if(BUILD_TESTING)
  # C++ unit-tests framework used.
  find_package(GTest CONFIG REQUIRED)
  include(GoogleTest)
  # Config folder
  get_filename_component(CONFIG_PATH config ABSOLUTE)
  # create the executable
  add_executable(test_${PROJECT_NAME}_cpp tests/main.cpp tests/unit_tests.cpp)
  # link to the created librairies and its dependencies
  target_link_libraries(test_${PROJECT_NAME}_cpp ${PROJECT_NAME} GTest::gtest)
  # create 2 macro: the path to the config file and the path to the data file
  target_compile_definitions(
      test_${PROJECT_NAME}_cpp
      PUBLIC
      CONFIG_PATH="${CONFIG_PATH}"
      TEST_PID_GAINS_YAML_FILE_PATH="${CONFIG_PATH}/test_pid_gains.yaml"
  )
  # declare the test as gtest
  gtest_add_tests(TARGET test_${PROJECT_NAME}_cpp)
endif()

#
# building documentation
#
add_documentation()

#
# Install and export.
#

# install the include directory
install(DIRECTORY include/ DESTINATION include)

# command to install the library and binaries
install(
  TARGETS ${all_targets}
  EXPORT ${PROJECT_NAME}Targets
  LIBRARY DESTINATION lib
  ARCHIVE DESTINATION lib
  RUNTIME DESTINATION bin
  INCLUDES
  DESTINATION include)

# install the python package too
get_python_install_dir(python_install_dir)
install(FILES config/test_pid_gains.yaml
        DESTINATION ${python_install_dir}/${PROJECT_NAME}/config)
install(
  DIRECTORY python/${PROJECT_NAME}
  DESTINATION "${python_install_dir}"
  PATTERN "*.pyc" EXCLUDE
  PATTERN "__pycache__" EXCLUDE)

# Export this package as a cmake package.
generate_cmake_package()
