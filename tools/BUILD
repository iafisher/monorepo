load("@rules_python//python:defs.bzl", "py_binary")


py_binary(
    name = "precommit",
    srcs = ["precommit.py"],
    deps = [
        ":check",
        "//common:pycommon",
    ],
)

py_binary(
    name = "fix",
    srcs = ["fix.py"],
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
