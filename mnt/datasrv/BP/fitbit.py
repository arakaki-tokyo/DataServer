import sqlite3
from .base import Base
from flask import Response
from datetime import datetime, timedelta, timezone
import pandas as pd
from enum import Enum, auto

hr_queries = {
    "1sec": 'select * from hr where timestamp between ? and ?',
    "1min": '''
        select timestamp, avg(value) as value
        from (
            select timestamp / 60 * 60 as timestamp, value
            from hr where timestamp between ? and ?
        )
        group by timestamp
        ''',
    # 10分間平均: date/hours/value
    "1month": '''
    select
        date,
        cast(timestamp - strftime("%s", date||'T00:00:00', '-9 hours') as real)
            /60/60 as hours,
        value
    from (
        select
            date(timestamp, 'unixepoch', '+9 hours') as date,
            timestamp,
            avg(value) as value
        from (
            select timestamp / 600 * 600 as timestamp, value
            from hr where timestamp between ? and ?)
        group by timestamp
    )
    '''
}


class Ext(Enum):
    json = auto()
    csv = auto()


class Fitbit(Base):

    def __init__(self):
        super().__init__("fitbit")

        self.get('/d/<detail_level>/<target_date>')(self.get_day)
        self.get('/m/<target_date>.<e>')(self.get_month)

    def check_extension(self, ext: str, accept=[Ext.json, Ext.csv]):
        exts = [e.name for e in accept]
        if ext in exts:
            return Ext[ext]
        else:
            message = f"file extension must be one of followings {exts}"
            return {"error": message}

    def check_isoformat(self, s: str):
        try:
            return datetime.fromisoformat(s)
        except ValueError as e:
            return {"error": str(e)}
        except TypeError:
            message = "'target-date' must be iso-formatted string \
                like YYYY-MM-DD"
            return {"error": message}

    def get_hr_range(
            self,
            q: str,
            start: datetime,
            range: timedelta) -> sqlite3.Cursor:
        end = start + range
        return self._get_db().execute(q, (start.timestamp(), end.timestamp()))

    def get_day(self, detail_level, target_date):
        if detail_level in ['1sec', '1min']:
            q = hr_queries[detail_level]
        else:
            return {"error": "'detail-level' must be '1sec' or '1min'"}

        maybe_datetime = self.check_isoformat(f'{target_date}T00:00+09:00')
        if isinstance(maybe_datetime, datetime):
            start = maybe_datetime
        else:
            return maybe_datetime

        range = timedelta(days=1)
        cur = self.get_hr_range(q, start, range)

        return {"dataset": [[row['timestamp'], row['value']] for row in cur]}

    def _get_next_month(
            self,
            d: datetime,
            tzinfo: timezone = None) -> datetime:
        '''
        Return datetime of next month with day1
        '''
        y, m = divmod(d.month, 12)
        return datetime(d.year + y, m + 1, 1, tzinfo=tzinfo)

    def get_month(self, target_date, e):
        acceptable_exts = [Ext.json, Ext.csv]
        ext = self.check_extension(e, acceptable_exts)
        if not isinstance(ext, Ext):
            return ext

        start = self.check_isoformat(f'{target_date}-01T00:00+09:00')
        if not isinstance(start, datetime):
            return {"error": "url format is YYYY-MM.<ext>"}

        end = self._get_next_month(start, timezone(timedelta(hours=9)))
        q = hr_queries['1month']

        df = pd.read_sql_query(
            sql=q,
            params=(start.timestamp(), end.timestamp()),
            con=self._get_db()
        ).pivot(index='date', columns='hours', values='value')

        if ext == Ext.json:
            return df.to_json(orient='split')
        elif ext == Ext.csv:
            return Response(df.to_csv(), mimetype='text/plain')
