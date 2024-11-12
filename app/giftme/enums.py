
from enum import Enum

class GenderEnum(Enum):
    MALE = 'male'
    FEMALE = 'female'

class ProfessionEnum(str, Enum):
    DEVELOPER = "developer"
    DESIGNER = "designer"
    MANAGER = "manager"
    TEACHER = "teacher"
    DOCTOR = "doctor"
    ENGINEER = "engineer"
    MARKETER = "marketer"
    WRITER = "writer"
    ARTIST = "artist"
    LAWYER = "lawyer"
    SCIENTIST = "scientist"
    NURSE = "nurse"
    UNEMPLOYED = "unemployed"
