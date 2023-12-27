from __future__ import annotations

from datetime import datetime
from typing import Literal, TypedDict

ProfileType = TypedDict(
    "ProfileType",
    {
        "full_name": str,
        "admission_number": str,
        "application_number": str,
        "father_name": str,
        "fee_category": str,
        "dob": str,
        "nationality": str,
        "religion": str,
        "local_address": str,
        "permanent_address": str,
        "city": str,
        "state": str,
        "zip_code": int,
        "emergency_contact": int,
        "email": str,
        "user_id": str,
        "class": str,
        "semester": str,
        "roll_no": int,
        "eligibility_number": str,
        "prn_number": int,
    },
)
SlotType = TypedDict(
    "SlotType",
    {
        "course_name": str,
        "course_type": Literal["PR", "PP"] | str,
        "course_code": str,
        "section": int,
        "room": str,
        "block": Literal["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"] | str,
        "pr": bool,
        "pp": bool,
    },
)

AlternativeArrangementData = TypedDict(
    "AlternativeArrangementType",
    {
        "date": datetime,
        "start_time": datetime,
        "end_time": datetime,
        "faculty_name": str,
        "alternate_faculty_name": str,
        "slot": SlotType,
    },
)

AlternativeArrangement = TypedDict(
    "AlternativeArrangement",
    {
        "Sun": list[AlternativeArrangementData],
        "Mon": list[AlternativeArrangementData],
        "Tue": list[AlternativeArrangementData],
        "Wed": list[AlternativeArrangementData],
        "Thu": list[AlternativeArrangementData],
        "Fri": list[AlternativeArrangementData],
        "Sat": list[AlternativeArrangementData],
    },
    total=False,
)

ArrangementData = TypedDict(
    "ArrangementData",
    {
        "date": datetime,
        "start_time": datetime,
        "end_time": datetime,
        "faculty_name": str,
        "slot": SlotType,
        "class": str,
    },
)

Arrangement = TypedDict(
    "Arrangement",
    {
        "Sun": list[ArrangementData],
        "Mon": list[ArrangementData],
        "Tue": list[ArrangementData],
        "Wed": list[ArrangementData],
        "Thu": list[ArrangementData],
        "Fri": list[ArrangementData],
        "Sat": list[ArrangementData],
    },
)

Credentials = TypedDict(
    "Credentials",
    {
        "admission_number": str,
        "password": str,
        "section": str | int,
    },
)

TimeTableGetData = TypedDict(
    "TimeTableGetData",
    {
        "timetable": Arrangement,
        "alternative_timetable": AlternativeArrangement,
    },
)

TimeTableReturnData = TypedDict(
    "TimeTableReturnData",
    {
        "start_time": datetime,
        "end_time": datetime,
        "faculty_name": str,
        "class": str,
        "course_name": str,
        "course_code": str,
        "course_type": str,
        "room": str,
    },
)
