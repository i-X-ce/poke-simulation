# poke-simulation

[PyBoy](https://github.com/Baekalfen/PyBoy)を使用して初代ポケモンであらゆるシミュレーションを高速で行います。確率計算や検証用途などに使用可能です。  
なお、本リポジトリで得られる結果はあくまで PyBoy 上で仮想的にシミュレーションされたものであり、実機での結果と必ずしも一致するとは限りませんのでご注意ください。

## 動作環境

- Python 3.11.4
- ライブラリ: [requirements.txt](./requirements.txt)

## ライブラリのインストール

このリポジトリで使用している Python ライブラリは[requirements.txt](./requirements.txt)にまとめられています。
以下を実行してライブラリのインストールを行ってください。

```
pip install -r requirements.txt
```

## 注意

このリポジトリに含まれる対戦データは、ROM・セーブデータを使用してローカルで計測されたものであり、再現にはそれらが必要です。ROM・セーブデータ・ステートデータ等は含まれていません。
