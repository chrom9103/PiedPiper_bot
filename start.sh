#!/bin/bash

# バックグラウンドで各Pythonスクリプトを起動
python dice.py &
python monitorVC.py &
python morce_cat.py &
python pin.py &
python word_game.py &

# すべてのバックグラウンドプロセスが終了するのを待つ
wait -n