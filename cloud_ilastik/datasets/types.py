import enum


@enum.unique
class ChannelType(enum.Enum):
    Intensity = "intensity"
    IndexedColor = "indexed"

    @classmethod
    def choices(cls):
        return tuple((item.name, item.value) for item in cls)

    @classmethod
    def values(cls):
        return tuple(item.value for item in cls)


@enum.unique
class ColorTable(enum.Enum):
    ILASTIK = "ilastik"
    RGB = "rgb"
    GRAYSCALE = "grayscale"
