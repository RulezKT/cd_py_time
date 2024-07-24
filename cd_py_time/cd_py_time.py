import math
from datetime import datetime

from cd_py_types import GregDate, LocalTime, ReqData
from zoneinfo import ZoneInfo

# 1 - local time, 0- UTC Time
# class TypeOfTime(Enum):
#     UTC = 0
#     Local = 1

SEC_IN_1_DAY: int = 86400
JD2000: int = 2451545


# returns offset in second
def calc_offset(req_data: ReqData) -> int:
    # print(req_data.time_zone_id)
    dt = (
        datetime(
            req_data.year,
            req_data.month,
            req_data.day,
            req_data.hours,
            req_data.minutes,
            tzinfo=ZoneInfo(req_data.time_zone_id),
        )
        .utcoffset()
        .total_seconds()
        # / 60
        # / 60
    )
    # print(dt)
    # print(dt.tzname())
    # print(dt.tzinfo.)
    # print(req_data.offset)

    return math.ceil(dt)


def convert_time(req_data: ReqData) -> tuple[int, GregDate, LocalTime]:
    # Violetta original
    # sec_from_jd2000 =  402_345_066.6
    # this.formula.personality_time_UTC  =  2012,10,1,6,30,1
    # this.formula.design_time_UTC   =  2012,7,1,22,56,56

    # Vio - Pers.Time: "1.10.2012 18:30" Des.Time: "2.7.2012 11:19"
    # 402_388_200

    pers_time_sec = 0
    pers_time_utc: GregDate = {}
    pers_time_local = LocalTime(
        year=0,
        month=0,
        day=0,
        hours=0,
        minutes=0,
        offset=0,
        place="",
        latitude=0,
        longitude=0,
        time_zone_id="",
    )

    # UTC
    if req_data.type_of_time == 0:
        # print("UTC")
        pers_time_utc = GregDate(
            year=req_data.year,
            month=req_data.month,
            day=req_data.day,
            hours=req_data.hours,
            minutes=req_data.minutes,
        )
        pers_time_sec = greg_sec(pers_time_utc)
        # 1 when we use DeltaT, 0 when not
        # TDT = UT + ΔT
        pers_time_sec += get_delta_t(pers_time_utc.year)

    # local
    # Если есть смещение часового пояса вычитаем его
    # if (pers_time.typeOfTime ==TypeOfTime.Local)
    else:
        # print("Local")
        if req_data.time_zone_id != "":
            tz_offset = calc_offset(req_data)
            if req_data.offset != tz_offset:
                req_data.offset = tz_offset
                print("google offset is wrong, using tzdata")
        pers_time_local = LocalTime(
            year=req_data.year,
            month=req_data.month,
            day=req_data.day,
            hours=req_data.hours,
            minutes=req_data.minutes,
            offset=req_data.offset,
            place=req_data.place,
            latitude=req_data.latitude,
            longitude=req_data.longitude,
            time_zone_id=req_data.time_zone_id,
        )
        # console.log(pers_time)
        # pers_time.pers_time_local.offset = reqData.offset
        pers_time_sec = greg_sec(pers_time_local)
        # console.log(sec_from_jd2000)
        # console.log(pers_time.pers_time_local.offset)
        pers_time_sec -= pers_time_local.offset

        # print(pers_time["pers_time_local"])
        pers_time_utc = sec_greg(pers_time_sec)
        # print(pers_time["pers_time_local"]["offset"])
        # print(pers_time_sec)  # 402388200
        # print(pers_time_utc)
        # 1 when we use DeltaT, 0 when not
        # TDT = UT + ΔT

        pers_time_sec += get_delta_t(pers_time_local.year)

    # console.log(pers_time)
    return math.ceil(pers_time_sec), pers_time_utc, pers_time_local


# отличная версия калькуляции, получаем Грег. дату в ET
# sec jd2000 to_greg_meeus , cut seconds from calculation
# V3 2024
def sec_greg(sec_from_jd2000: int) -> GregDate:
    # JD2000 = 2451545.0  # 12:00 UT on January 1, 2000
    # получаем Julian Day
    jdn = JD2000 + sec_from_jd2000 / SEC_IN_1_DAY

    jdn += 0.5

    A = None

    Z = math.trunc(jdn)

    F = jdn - Z

    if Z < 2299161:
        A = Z
    else:
        alpha = math.trunc((Z - 1867216.25) / 36524.25)
        A = Z + 1 + alpha - math.trunc(alpha / 4)

    B = math.trunc(A + 1524)

    C = math.trunc((B - 122.1) / 365.25)

    D = math.trunc(365.25 * C)

    E = math.trunc((B - D) / 30.6001)

    day = B - D - math.trunc(30.6001 * E) + F

    month = None

    if E < 0 or E > 15:
        print("sec_jd2000_to_greg_meeus, unacceptable value of E")
        raise ValueError

    if E < 14:
        month = E - 1
    else:
        month = E - 13

    year = C - 4716 if month > 2 else C - 4715

    hour = (day - math.trunc(day)) * 24

    day = math.trunc(day)

    minute = (hour - math.trunc(hour)) * 60

    hour = math.trunc(hour)

    minute = math.trunc(minute)

    return GregDate(year=year, month=month, day=day, hours=hour, minutes=minute)


def greg_sec(greg_date: GregDate) -> int:
    hour_dec = greg_date.hours + greg_date.minutes / 60
    jd = swe_julday(greg_date.year, greg_date.month, greg_date.day, hour_dec)
    return math.ceil((jd - JD2000) * SEC_IN_1_DAY)


def swe_julday(year, month, day, hour: float) -> float:
    u = year
    if month < 3:
        u -= 1
    u0 = u + 4712.0
    u1 = month + 1.0
    if u1 < 4:
        u1 += 12.0
    jd = (
        math.floor(u0 * 365.25)
        + math.floor(30.6 * u1 + 0.000001)
        + day
        + hour / 24.0
        - 63.5
    )

    u2 = math.floor(abs(u) / 100) - math.floor(abs(u) / 400)
    if u < 0.0:
        u2 = -u2
    jd = jd - u2 + 2
    if (
        (u < 0.0)
        and (u / 100 == math.floor(u / 100))
        and (u / 400 != math.floor(u / 400))
    ):
        jd -= 1

    return jd


"""	
// delta_t observations started at 1620 and now it is 2017
// so we have 398 records for now
// each record is the year and a number of seconds
// [0] record corresponds to year 1620
// https://www.staff.science.uu.nl/~gent0113/deltat/deltat.htm
// ftp://maia.usno.navy.mil/ser7/deltat.data

/*
http://astro.ukho.gov.uk/nao/miscellanea/DeltaT/
https://ru.wikipedia.org/wiki/%D0%94%D0%B5%D0%BB%D1%8C%D1%82%D0%B0_T
https://eclipse.gsfc.nasa.gov/SEhelp/deltatpoly2004.html
https://en.wikipedia.org/wiki/%CE%94T

struct delta_t_table_struct{
    int year;
    double seconds;
};
"""

full_delta_t_table = [
    [1950, 29.15],
    [1951, 29.57],
    [1952, 29.97],
    [1953, 30.36],
    [1954, 30.72],
    [1955, 31.07],
    [1956, 31.35],
    [1957, 31.68],
    [1958, 32.18],
    [1959, 32.68],
    [1960, 33.15],
    [1961, 33.59],
    [1962, 34.0],
    [1963, 34.47],
    [1964, 35.03],
    [1965, 35.73],
    [1966, 36.54],
    [1967, 37.43],
    [1968, 38.29],
    [1969, 39.2],
    [1970, 40.18],
    [1971, 41.17],
    [1972, 42.23],
    [1973, 43.37],
    [1974, 44.49],
    [1975, 45.48],
    [1976, 46.46],
    [1977, 47.52],
    [1978, 48.53],
    [1979, 49.59],
    [1980, 50.54],
    [1981, 51.38],
    [1982, 52.17],
    [1983, 52.96],
    [1984, 53.79],
    [1985, 54.34],
    [1986, 54.87],
    [1987, 55.32],
    [1988, 55.82],
    [1989, 56.3],
    [1990, 56.86],
    [1991, 57.57],
    [1992, 58.31],
    [1993, 59.12],
    [1994, 59.99],
    [1995, 60.78],
    [1996, 61.63],
    [1997, 62.3],
    [1998, 62.97],
    [1999, 63.47],
    [2000, 63.83],
    [2001, 64.09],
    [2002, 64.3],
    [2003, 64.47],
    [2004, 64.57],
    [2005, 64.69],
    [2006, 64.85],
    [2007, 65.15],
    [2008, 65.46],
    [2009, 65.78],
    [2010, 66.07],
    [2011, 66.32],
    [2012, 66.6],
    [2013, 66.91],
    [2014, 67.28],
    [2015, 67.64],
    [2016, 68.1],
    [2017, 69.18],
    [2018, 69.18],
    [2019, 69.18],
    [2020, 69.18],
    [2021, 69.18],
    [2022, 69.18],
    [2023, 69.2],
    [2024, 69.18],
]

"""	
//https://eclipse.gsfc.nasa.gov/SEhelp/deltaT.html
//This parameter is known as delta-T or ΔT (ΔT = TDT - UT).
// for delta_t calculations we use
// https://eclipse.gsfc.nasa.gov/SEcat5/deltatpoly.html
// algorithms
"""


def __calculate_delta_t(year):
    delta_t_sec = None

    # before year 1620 (observations started from 1620, before were only estimations)
    if year < 1620:
        if year < -500:
            delta_t_sec = -20 + 32 * math.pow((year - 1820) / 100, 2)
            return delta_t_sec
        elif year >= -500 and year <= 500:
            delta_t_sec = (
                10583.6
                - (1014.41 * year) / 100
                + 33.78311 * math.pow(year / 100, 2)
                - 5.952053 * math.pow(year / 100, 3)
                - 0.1798452 * math.pow(year / 100, 4)
                + 0.022174192 * math.pow(year / 100, 5)
                + 0.0090316521 * math.pow(year / 100, 6)
            )
            return delta_t_sec
        elif year > 500 and year <= 1600:
            delta_t_sec = (
                1574.2
                - (556.01 * (year - 1000)) / 100
                + 71.23472 * math.pow((year - 1000) / 100, 2)
                + 0.319781 * math.pow((year - 1000) / 100, 3)
                - 0.8503463 * math.pow((year - 1000) / 100, 4)
                - 0.005050998 * math.pow((year - 1000) / 100, 5)
                + 0.0083572073 * math.pow((year - 1000) / 100, 6)
            )
            return delta_t_sec
        else:
            # from 1600 to 1620
            delta_t_sec = (
                120
                - 0.9808 * (year - 1600)
                - 0.01532 * math.pow(year - 1600, 2)
                + math.pow(year - 1600, 3) / 7129
            )
            return delta_t_sec

    if year >= 1620 and year <= 1700:
        delta_t_sec = (
            120
            - 0.9808 * (year - 1600)
            - 0.01532 * math.pow(year - 1600, 2)
            + math.pow(year - 1600, 3) / 7129
        )
        return delta_t_sec

    if year > 1700 and year <= 1800:
        delta_t_sec = (
            8.83
            + 0.1603 * (year - 1700)
            - 0.0059285 * math.pow(year - 1700, 2)
            + 0.00013336 * math.pow(year - 1700, 3)
            - math.pow(year - 1700, 4) / 1174000
        )
        return delta_t_sec

    if year > 1800 and year <= 1860:
        delta_t_sec = (
            13.72
            - 0.332447 * (year - 1800)
            + 0.0068612 * math.pow(year - 1800, 2)
            + 0.0041116 * math.pow(year - 1800, 3)
            - 0.00037436 * math.pow(year - 1800, 4)
            + 0.0000121272 * math.pow(year - 1800, 5)
            - 0.0000001699 * math.pow(year - 1800, 6)
            + 0.000000000875 * math.pow(year - 1800, 7)
        )
        return delta_t_sec

    if year > 1860 and year <= 1900:
        delta_t_sec = (
            7.62
            + 0.5737 * (year - 1860)
            - 0.251754 * math.pow(year - 1860, 2)
            + 0.01680668 * math.pow(year - 1860, 3)
            - 0.0004473624 * math.pow(year - 1860, 4)
            + math.pow(year - 1860, 5) / 233174
        )
        return delta_t_sec

    if year > 1900 and year <= 1920:
        delta_t_sec = (
            -2.79
            + 1.494119 * (year - 1900)
            - 0.0598939 * math.pow(year - 1900, 2)
            + 0.0061966 * math.pow(year - 1900, 3)
            - 0.000197 * math.pow(year - 1900, 4)
        )
        return delta_t_sec

    if year > 1920 and year <= 1941:
        delta_t_sec = (
            21.2
            + 0.84493 * (year - 1920)
            - 0.0761 * math.pow(year - 1920, 2)
            + 0.0020936 * math.pow(year - 1920, 3)
        )
        return delta_t_sec

    if year > 1941 and year <= 1961:
        delta_t_sec = (
            29.07
            + 0.407 * (year - 1950)
            - math.pow(year - 1950, 2) / 233.0
            + math.pow(year - 1950, 3) / 2547.0
        )
        return delta_t_sec

    if year > 1961 and year <= 1986:
        delta_t_sec = (
            45.45
            + 1.067 * (year - 1975)
            - math.pow(year - 1975, 2) / 260.0
            - math.pow(year - 1975, 3) / 718.0
        )
        return delta_t_sec

    if year > 1986 and year <= 2005:
        delta_t_sec = (
            63.86
            + 0.3345 * (year - 2000)
            - 0.060374 * math.pow(year - 2000, 2)
            + 0.0017275 * math.pow(year - 2000, 3)
            + 0.000651814 * math.pow(year - 2000, 4)
            + 0.00002373599 * math.pow(year - 2000, 5)
        )
        return delta_t_sec

    if year > 2005 and year <= 2050:
        delta_t_sec = (
            62.92 + 0.32217 * (year - 2000) + 0.005589 * math.pow(year - 2000, 2)
        )
        return delta_t_sec

    if year > 2050 and year <= 2150:
        delta_t_sec = (
            -20 + 32 * math.pow((year - 1820) / 100.0, 2) - 0.5628 * (2150 - year)
        )
        return delta_t_sec

    if year > 2150:
        delta_t_sec = -20 + 32 * math.pow((year - 1820) / 100.0, 2)
        return delta_t_sec

    return -1


def get_delta_t(year):
    first_year = full_delta_t_table[0][0]
    last_year = full_delta_t_table[-1][0]
    if year < first_year or year > last_year:
        return __calculate_delta_t(year)

    return full_delta_t_table[year - first_year][1]


if __name__ == "__main__":
    temp_date = {
        "year": 1978,
        "month": 5,
        "day": 17,
        "hours": 15,
        "minutes": 47,
        "seconds": 0,
    }
    print(greg_sec(temp_date))

    temp_date = {
        "year": 2012,
        "month": 10,
        "day": 1,
        "hours": 8,
        "minutes": 30,
        "seconds": 0,
    }
    print(greg_sec(temp_date))

    temp_date = {
        "year": 2012,
        "month": 10,
        "day": 1,
        "hours": 6,
        "minutes": 29,
        "seconds": 50,
    }
    print(greg_sec(temp_date))

    # Vio original
    # sec_from_jd2000 =  402_345_066.6
    # this.formula.personality_time_UTC  =  2012,10,1,6,30,1
    # this.formula.design_time_UTC   =  2012,7,1,22,56,56
