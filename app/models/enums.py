from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    coach = "coach"


class SkillLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"


class LessonType(str, Enum):
    club = "club"
    private = "private"


class LessonStatus(str, Enum):
    draft = "draft"
    set = "set"
    executed = "executed"
    invoiced = "invoiced"


class LessonPaymentStatus(str, Enum):
    open = "open"
    paid = "paid"


class StrokeCode(str, Enum):
    forehand = "forehand"
    backhand = "backhand"
    volley = "volley"
    smash = "smash"
    serve = "serve"
    lob = "lob"
    drop_shot = "drop_shot"
    bandeja = "bandeja"
    vibora = "vibora"
    chiquita = "chiquita"


class InvoiceStatus(str, Enum):
    draft = "draft"
    issued = "issued"
    paid = "paid"
    void = "void"
