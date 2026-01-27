from enum import Enum


class MemoryStrategyEnums(str, Enum):
    SEMANTIC = "SEMANTIC"
    USER_PREFERENCE = "USER_PREFERENCE"
    SUMMARY = "SUMMARY"

class MemoryActionType(str, Enum):
    add = "add"
    update = "update"
    skip = "skip"