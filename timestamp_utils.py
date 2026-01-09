import datetime
import logging
import re


def make_timestamp(value: str):
    """Construct timestamp from different datetime formats."""
    values = []
    date_value = None
    date_stamp = None
    date_start = 315522000

    splitter = None
    try:
        if value:
            if re.match(r'\d{4}[-:]?.\d[-:]?.\d[ T]?.{,2}:.{,2}:.{,2}', value):
                values.append(value[:10])
                values.append(value[11:19])
                values.append(value[20:])
                if re.match(r'\d{4}-.\d-.\d[ T]?.{,2}:.{,2}:.{,2}', value):
                    splitter = '-'
                elif re.match(r'\d{4}:.\d:.\d[ T]?.{,2}:.{,2}:.{,2}', value):
                    splitter = ':'

                if splitter:
                    dt = values[0].split(splitter)
                    yy = int(dt[0])
                    if yy > 1980:
                        mm = int(dt[1])
                        if mm < 1 or mm > 12:
                            mm = 1

                        dd = int(dt[2])
                        if dd < 1 or dd > 31:
                            dd = 1

                        d = datetime.date(yy, mm, dd)
                        tm = values[1].split(':')

                        sh = tm[0]
                        if not sh.isspace():
                            h = int(sh)
                            if h > 23:
                                h = 23
                            elif h < 0:
                                h = 1
                        else:
                            h = 0

                        sm = tm[1]
                        if not sm.isspace():
                            m = int(sm)
                            if m > 59:
                                m = 59
                            elif m < 0:
                                m = 1
                        else:
                            m = 0

                        st = tm[2]
                        if not st.isspace():
                            s = int(st)
                            if s > 59:
                                s = 59
                            elif s < 0:
                                s = 1
                        else:
                            s = 1

                        t = datetime.time(h, m, s)
                        date_value = datetime.datetime.combine(d, t)

            if date_value:
                date_stamp = int(date_value.timestamp())
                if int(date_stamp) < date_start:
                    date_stamp = None

    except Exception as e:
        print(f"can't convert {value} to .timestamp {date_stamp} error: {e}")
        logging.error(f"can't convert {value} to .timestamp {date_stamp} error: {e}")

    return date_stamp
