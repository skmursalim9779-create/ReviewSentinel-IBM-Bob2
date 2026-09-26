from . import complexity, injection, path_traversal, secrets, unsafe_eval, weak_crypto

ALL_SCANNERS = [
    ("secrets", secrets.scan),
    ("injection", injection.scan),
    ("unsafe_eval", unsafe_eval.scan),
    ("weak_crypto", weak_crypto.scan),
    ("path_traversal", path_traversal.scan),
    ("complexity", complexity.scan),
]
