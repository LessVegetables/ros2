cmake_minimum_required(VERSION 3.8)
project(localization_case)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})
install(PROGRAMS
  scripts/measure_localization.py
  scripts/make_localization_report.py
  DESTINATION lib/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(test_metrics test/test_metrics.py TIMEOUT 60)
  ament_add_pytest_test(test_launch test/test_launch.py TIMEOUT 60)
endif()

ament_package()
