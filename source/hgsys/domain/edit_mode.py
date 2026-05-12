from enum import IntEnum


class EditMode(IntEnum):
    NONE = 0
    APPEND = 1
    MODIFY = 2
    INHIBIT = 3


_EDITABLE = {
    EditMode.NONE: False,
    EditMode.APPEND: True,
    EditMode.MODIFY: True,
    EditMode.INHIBIT: False,
}

_COLOR = {
    EditMode.NONE: "black",
    EditMode.APPEND: "red",
    EditMode.MODIFY: "red",
    EditMode.INHIBIT: "black",
}


def is_editable(mode: EditMode) -> bool:
    return _EDITABLE[mode]


def color_for(mode: EditMode) -> str:
    return _COLOR[mode]
