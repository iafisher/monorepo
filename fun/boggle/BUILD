load("@rules_python//python:defs.bzl", "py_binary")


py_binary(
    name = "boggle",
    srcs = ["boggle.py"],
    data = glob(["words/*"]),
)
