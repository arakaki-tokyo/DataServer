# Data Server
おれが個人的に使うデータを配信する

## Architecture
関連するデータ毎にBlueprintに分割し、それぞれSQLiteファイルを持つ。
Blueprintは`datasrv`パッケージの`BP`サブパッケージにモジュール(ファイル)として追加する。
`base.py`を参照されたし。

## Development
### 実行方法
```
FLASK_APP=datasrv \
FLASK_ENV=development \
flask run -h 0.0.0.0 -p 80
```
開発環境ではflaskからcronは実行されない


### コマンドラインから DB 初期化
flaskチュートリアルの流れで作ったものの、たぶん使う機会はない。
一応schemaは`datasrv/schema`に入れとくと見返すことがあるかも。
```
FLASK_APP=flaskr \
flask <blueprint name> initdb
```