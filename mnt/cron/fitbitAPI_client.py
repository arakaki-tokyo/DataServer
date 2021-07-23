'''cron用fitbit APIクライアント(OAuth 2.0 Authorization Code Grant対応)

- 実行時に当ファイルのディレクトリに移動する
- DBとして../instance/fitbit.sqliteを使用する
- logディレクトリとして./logを使用する
    - アクセスログはmylog関数から出力される
    - エラーログはcrontabのリダイレクトから出力される
- 設定ファイルとして./config.jsonを使用する
    - 内容は以下
    {
        "access_token": "", 
        "refresh_token": "", 
        "client_id": "", 
        "client_secret": ""
    }

'''

import os
from datetime import date, datetime, time, timedelta, timezone
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib import parse
from http.client import HTTPResponse
import json
import base64
import sqlite3


def mylog(s):

    this_file_name = os.path.basename(__file__)
    formatted_date = date.today().strftime("%Y-%m")
    now = datetime.now(timezone(timedelta(hours=9)))
    log_file = f'{this_file_name}_{formatted_date}.log'
    log_dir = f'{os.path.dirname(__file__)}/log'
    log_file_path = f'{log_dir}/{log_file}'

    if not os.path.exists(log_dir):
        os.mkdir(log_dir)

    with open(log_file_path, 'a') as f:
        f.write(f'{now.strftime("%Y-%m-%d %H:%M:%S")}: {s}\n')


class FAPI(Request):
    base_url = "https://api.fitbit.com/1/user/-/"

    def __init__(self):
        super().__init__(self.base_url)
        self.set_config()

    def set_config(self):
        with open('config.json') as f:
            self.config = json.load(f)

        self.add_header(
            "Authorization",
            f'Bearer {self.config["access_token"]}')

    def get_hr(
        self,
        date: str,
        end_date: str = None,
        start_time: str = None,
        end_time: str = None
    ) -> HTTPResponse:
        '''
        See https://dev.fitbit.com/build/reference/web-api/heart-rate/

        Args:
            date: The date, in the format yyyy-MM-dd or today.
            end_date: Optional. The date, in the format yyyy-MM-dd.
            start_time: Optional. The start of the period, in the format HH:mm.
            end_time: Optional. The end of the period, in the format HH:mm.

        Returns:
            HTTPResponse Objects
        '''

        url = self.base_url
        if (start_time is None) ^ (end_time is None):
            return

        if end_date is None:
            url += f'activities/heart/date/{date}/1d/1sec'
        else:
            url += f'activities/heart/date/{date}/{end_date}/1sec'

        if start_time is not None:
            url += f'/time/{start_time}/{end_time}'

        url += '.json'
        self.full_url = url
        return self.open()

    def open(self):
        try:
            res = urlopen(self)
            return res
        except HTTPError as e:
            if e.code == 401:
                try:
                    FAPI().refresh()
                    self.set_config()
                    return self.open()
                except HTTPError as e:
                    mylog(e)
            else:
                mylog(e)
                mylog(e.read())

    def get_credentials(self):
        cred = f'{self.config["client_id"]}:{self.config["client_secret"]}'
        return str(base64.b64encode(cred.encode()), encoding='utf-8')

    def refresh(self):
        self.add_header('Authorization', f'Basic {self.get_credentials()}')
        self.add_header('Content-Type', 'application/x-www-form-urlencoded')
        data = {"grant_type": "refresh_token",
                "refresh_token": self.config['refresh_token']}
        self.data = parse.urlencode(data).encode('ascii')
        self.full_url = 'https://api.fitbit.com/oauth2/token'

        res = self.open()
        body = json.load(res)

        self.config['access_token'] = body['access_token']
        self.config['refresh_token'] = body['refresh_token']

        with open('config.json', "w") as f:
            json.dump(self.config, f)

        mylog("Access Token updated.")


def get_db() -> sqlite3.Connection:
    return sqlite3.connect("../instance/fitbit.sqlite")


def insert_db(d: tuple, con: sqlite3.Connection):
    q = 'insert or ignore into hr values(?, ?)'
    con.execute(q, d)


def fetch(date: date, start: time):
    '''
    `date`の日付の`start`以降のデータを取得しDBにインサート
    '''
    res = FAPI().get_hr(
        date=date.isoformat(),
        start_time=start.strftime("%H:%M"),
        end_time="23:59")
    mylog(f'fetch url: {res.url}')
    dataset = json.load(res)["activities-heart-intraday"]['dataset']
    params = list()
    for data in dataset:
        iso_format = f'{date}T{data["time"]}+09:00'
        timestamp = int(datetime.fromisoformat(iso_format).timestamp())
        params.append((timestamp, data["value"]))

    con = get_db()
    con.executemany('insert or ignore into hr values(?, ?)', params)
    con.commit()
    con.close()


def main():
    JST = timezone(timedelta(hours=9))
    now = datetime.now(JST)
    # 最新のレコード取得
    con = get_db()
    latest_timestamp = con.execute(
        'select max(timestamp) from hr').fetchone()[0]
    con.close()
    latest_datetime = datetime.fromtimestamp(latest_timestamp, JST)

    working_date = latest_datetime.date()
    working_time = latest_datetime.time()
    # 最新レコードの日付が実行日より前の間
    while working_date < now.date():
        # 最新レコードから一日単位で取得
        fetch(working_date, working_time)

        if working_date == latest_datetime.date():
            working_time = time()
        working_date += timedelta(days=1)
    else:
        # 実行日の現在時刻まで取得
        fetch(working_date, working_time)


if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    main()
