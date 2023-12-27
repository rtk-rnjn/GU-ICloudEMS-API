from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from bs4.element import Tag

if TYPE_CHECKING:
    from .typehints import (
        AlternativeArrangement,
        Arrangement,
        ProfileType,
        SlotType,
        TimeTableGetData,
    )

try:
    import lxml  # noqa: F401  # pylint: disable=unused-import  # type: ignore

    HTML_PARSER = "lxml"
except ImportError:
    HTML_PARSER = "html.parser"


class HTMLParser(ABC):
    def __init__(self, html_source: str) -> None:
        self.html_source = html_source
        self.__soup = BeautifulSoup(html_source, HTML_PARSER)

    @property
    def soup(self) -> BeautifulSoup:
        return self.__soup

    @property
    def text(self) -> str:
        return self.__soup.get_text()

    @property
    def title(self) -> str:
        return self.__soup.title.string  # type: ignore

    @property
    def body(self) -> Tag:
        return self.__soup.find("body")  # type: ignore

    @abstractmethod
    def get_data(self) -> ...:
        ...


class ProfileParser(HTMLParser):
    @property
    def name(self) -> str:
        span = self.body.find("span", **{"class": "middle"})  # type: ignore
        return str(span.text)  # type: ignore

    @staticmethod
    def _try_int(value: str) -> int | str:
        if value is None:
            return "NA"

        value = ProfileParser._remove_extra_spaces(value)
        try:
            return int(value)
        except ValueError:
            return value.strip(" ")

    @staticmethod
    def _remove_extra_spaces(value: str) -> str:
        return " ".join(value.split())

    def get_data(self) -> ProfileType:
        data: ProfileType = {}  # type: ignore
        for div in [
            *self.body.find_all("div", **{"class": "profile-user-info"}),  # type: ignore
            *self.body.find_all("div", **{"class": "profile-info-row"}),  # type: ignore
        ]:
            assert isinstance(div, Tag)

            name = div.find("div", **{"class": "profile-info-name"})  # type: ignore
            value = div.find("div", **{"class": "profile-info-value"})  # type: ignore

            data[
                name.string.strip().lower().replace(" ", "_")  # type: ignore
            ] = ProfileParser._try_int(
                value.text.strip().replace("\n", "").replace("\t", " ")  # type: ignore
            )

        data["full_name"] = self.name

        data["father_name"] = data.pop("father/guardian_name")  # type: ignore
        data.pop("date_of_admission", None)  # type: ignore
        data["local_address"] = data.pop("local_/_present_address")  # type: ignore
        data["prn_number"] = data.pop("prn_no.")  # type: ignore
        data["eligibility_number"] = data.pop("eligibility_number:")  # type: ignore
        return data

    def create_sql_query(self, semicolon: bool = False) -> str:
        query = """INSERT INTO students ({}) VALUES ({}) ON CONFLICT DO NOTHING RETURNING id"""
        data = self.get_data()
        columns = ", ".join(data.keys())
        values = ", ".join(
            repr(value) if isinstance(value, str) else str(value)
            for value in data.values()
        )

        if semicolon:
            return f"{query.format(columns, values)};"

        return query.format(columns, values)


class TableParser(HTMLParser):
    def get_table(self, index: int = 0) -> Tag:
        return self.body.find_all("table")[index]


class _TimeTableParser(TableParser):
    def get_main_timetable_details(self) -> Tag:
        return self.get_table(0)

    def get_alternative_timetable_details(self) -> Tag:
        return self.get_table(1)

    def get_timetable_details(self) -> Tag:
        return self.get_table(2)


class _SlotParser:
    def __init__(self, raw_text) -> None:
        self._raw_text = raw_text
        self.course_name: str = ""
        self.course_type: str = ""
        self.course_code: str = ""
        self.section: str = ""
        self.room: str = ""
        self.block: str = ""

        self._parse()

    def __repr__(self) -> str:
        return (
            f"<SlotParser course_name={self.course_name!r} course_type={self.course_type!r} "
            f"course_code={self.course_code!r} section={self.section!r} room={self.room!r} block={self.block!r}>"
        )

    def _parse_rest(self) -> None:
        if "PR" in self._raw_text:
            self._pr = True
            self._raw_text = self._raw_text.replace("PR", "").strip()
        if "PP" in self._raw_text:
            self._pp = True
            self._raw_text = self._raw_text.replace("PP", "").strip()

    def _parse_course_name(self):
        self.course_name = self._raw_text[: self._raw_text.find("(")].strip()
        self._raw_text = self._raw_text.replace(self.course_name, "").strip()

    def _parse_course_type(self):
        index = self._raw_text.find(")")
        self.course_type = self._raw_text[index - 2 : index].strip()
        self._raw_text = self._raw_text.replace(self.course_type, "").strip()

    def _parse_course_code(self):
        regex = re.compile(r"([A-Z0-9]{8})")
        if match := regex.search(self._raw_text):
            self.course_code = match.group()
            self._raw_text = self._raw_text.replace(self.course_code, "").strip()

    def _parse_room(self):
        self._raw_text = self._raw_text.replace("GU_", "")
        regex = re.compile(r"([A-Z]{1})\-([0-9]{3})")
        if match := regex.search(self._raw_text):
            self.room = match[0]
            self.block = match[1].replace(self.room, "").strip()
            self._raw_text = self._raw_text.replace(match.group(), "").strip()

    def _parse_section(self):
        # catch remaining int
        regex = re.compile(r"([0-9]+)")
        if match := regex.search(self._raw_text):
            self.section = match.group()
            self._raw_text = self._raw_text.replace(match.group(), "").strip()

    def _parse(self) -> None:
        self._parse_course_name()
        self._parse_course_type()
        self._parse_course_code()
        self._parse_room()
        self._parse_rest()
        self._parse_section()

    def to_dict(self) -> SlotType:
        return {
            "course_name": self.course_name,
            "course_type": self.course_type,
            "course_code": self.course_code,
            "section": ProfileParser._try_int(self.section),  # type: ignore
            "room": self.room,
            "block": self.block,
        }

    @property
    def sql(self) -> str:
        return f"""
            INSERT INTO slots 
                (course_name, course_type, course_code, section, room, block)

            VALUES 
                (
                    {self.course_name!r},
                    {self.course_type!r},
                    {self.course_code!r},
                    {self.section},
                    {self.room!r},
                    {self.block!r}
                )

            ON CONFLICT DO UPDATE SET
                course_name = {self.course_name!r},
                course_type = {self.course_type!r},
                course_code = {self.course_code!r},
                section = {self.section},
                room = {self.room!r},
                block = {self.block!r}

            RETURNING id
        """

    @staticmethod
    def from_dict_to_sql(data: SlotType) -> str:
        return f"""
            INSERT OR REPLACE INTO slots 
                (course_name, course_type, course_code, section, room, block)

            VALUES 
                ({data["course_name"]!r}, {data["course_type"]!r}, {data["course_code"]!r}, {data["section"]}, {data["room"]!r}, {data["block"]!r})

            ON CONFLICT DO UPDATE SET 
                course_name = {data["course_name"]!r},
                course_type = {data["course_type"]!r},
                course_code = {data["course_code"]!r},
                section = {data["section"]},
                room = {data["room"]!r},
                block = {data["block"]!r}

            RETURNING id
        """


class TimeTableParser(_TimeTableParser):
    class_name: str

    def __set_class_name(self, raw) -> str:
        if hasattr(self, "class_name"):
            return self.class_name

        raw_str = raw
        raw_str = raw_str.split("/")[0]
        raw_str = raw_str.split("for")[-1]

        self.class_name = raw_str.strip()

        return self.class_name

    def get_date_range(self) -> dict:
        thread = self.get_main_timetable_details().find("thead")
        tr = thread.find("tr")  # type: ignore

        raw_text = tr.text  # type: ignore
        self.__set_class_name(raw_text)
        raw_range = raw_text.split("/")[-1]
        # " Date : 18 Dec 2023 To 24 Dec 2023"
        raw_range = raw_range[raw_range.find(":") + 1 :].strip()

        start, end = raw_range.split("To")
        start = start.strip()
        end = end.strip()

        start = datetime.strptime(start, "%d %b %Y")
        end = datetime.strptime(end, "%d %b %Y")

        return {
            "Mon": start,
            "Tue": start + timedelta(days=1),
            "Wed": start + timedelta(days=2),
            "Thu": start + timedelta(days=3),
            "Fri": start + timedelta(days=4),
            "Sat": start + timedelta(days=5),
            "Sun": end,
        }

    def get_alternative_timetable(self) -> AlternativeArrangement:
        table = self.get_alternative_timetable_details()
        data: AlternativeArrangement = {
            "Mon": [],
            "Tue": [],
            "Wed": [],
            "Thu": [],
            "Fri": [],
            "Sat": [],
            "Sun": [],
        }
        for tr in table.find_all("tr")[1:]:
            assert isinstance(tr, Tag)

            day: str = tr.find("td").text.strip()  # type: ignore
            assert day in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

            if day not in data:
                data[day] = []

            date = tr.find_all("td")[1].text.strip()
            date_object = datetime.strptime(date, "%Y-%m-%d")

            start_time, end_time = tr.find_all("td")[2].text.strip().split("-")
            if start_time.strip():
                start_time_object = date_object + timedelta(
                    hours=int(start_time.split(":")[0]),
                    minutes=int(start_time.split(":")[1]),
                )
            else:
                start_time_object = None

            if end_time.strip():
                end_time_object = date_object + timedelta(
                    hours=int(end_time.split(":")[0]),
                    minutes=int(end_time.split(":")[1]),
                )
            else:
                end_time_object = None

            data[day].append(
                {
                    "date": TimeTableParser._datetime_to_sqlite_string(date_object),
                    "start_time": TimeTableParser._datetime_to_sqlite_string(
                        start_time_object
                    ),
                    "end_time": TimeTableParser._datetime_to_sqlite_string(
                        end_time_object
                    ),
                    "faculty_name": tr.find_all("td")[3].text.strip(),
                    "alternate_faculty_name": tr.find_all("td")[4].text.strip(),
                    "slot": _SlotParser(tr.find_all("td")[5].text.strip()).to_dict(),
                    "class": self.class_name,
                }
            )

        return data

    def get_timetable(self) -> Arrangement:
        table = self.get_timetable_details()
        data: Arrangement = {
            "Mon": [],
            "Tue": [],
            "Wed": [],
            "Thu": [],
            "Fri": [],
            "Sat": [],
            "Sun": [],
        }
        date_range = self.get_date_range()
        for tr in table.find_all("tr")[1:]:
            assert isinstance(tr, Tag)

            day: str = tr.find("td").text.strip()  # type: ignore
            assert day in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

            if day not in data:
                data[day] = []

            date = date_range[day]
            start_time, end_time = tr.find_all("td")[1].text.strip().split("-")

            if start_time.strip():
                start_time_object = date + timedelta(
                    hours=int(start_time.split(":")[0]),
                    minutes=int(start_time.split(":")[1]),
                )
            else:
                start_time_object = None

            if end_time.strip():
                end_time_object = date + timedelta(
                    hours=int(end_time.split(":")[0]),
                    minutes=int(end_time.split(":")[1]),
                )
            else:
                end_time_object = None

            data[day].append(
                {
                    "date": TimeTableParser._datetime_to_sqlite_string(date),
                    "start_time": TimeTableParser._datetime_to_sqlite_string(
                        start_time_object
                    ),
                    "end_time": TimeTableParser._datetime_to_sqlite_string(
                        end_time_object
                    ),
                    "faculty_name": tr.find_all("td")[2].text.strip(),
                    "slot": _SlotParser(tr.find_all("td")[3].text.strip()).to_dict(),
                    "class": self.class_name,
                }
            )

        return data

    def get_data(self) -> TimeTableGetData:
        return {
            "timetable": self.get_timetable(),
            "alternative_timetable": self.get_alternative_timetable(),
        }

    @staticmethod
    def _datetime_to_sqlite_string(dt: datetime | None) -> str | None:
        return None if dt is None else dt.strftime("%Y-%m-%d %H:%M:%S")
