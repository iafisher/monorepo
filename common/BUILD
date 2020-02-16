load("@rules_python//python:defs.bzl", "py_library", "py_test")


package(default_visibility = ["//visibility:public"])

py_library(
    name = "pycommon",
    srcs = ["pycommon.py"],
)

py_test(
    name = "pycommon_test",
    srcs = ["pycommon_test.py"],
    deps = [":pycommon"],
    size = "small",
)
