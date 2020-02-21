load("@rules_python//python:defs.bzl", "py_binary")


py_binary(
    name = "precommit",
    srcs = ["precommit.py"],
    deps = [
        ":check",
        "//common:pycommon",
    ],
)

py_library(
    name = "check",
    srcs = ["check.py"],
    deps = ["//common:pycommon"],
)
