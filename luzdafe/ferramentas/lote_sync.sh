#!/bin/sh
# uso: lote_sync.sh id1 id2 ...  -> ASR + render sincronizado em v3/
cd /home/claude/serie
for id in "$@"; do
  SRC=/home/claude/primeiro-contato-midia/luzdafe/v2/$id.mp4
  ffmpeg -v error -y -i $SRC -ac 1 -ar 16000 asr/$id.wav
  python3 asr_words.py asr/$id.wav asr/$id.json > /dev/null
  python3 bin/pagina_sync.py historias21_dados.json $id $SRC asr/$id.json v3/$id.mp4 > logs_$id.txt 2>&1
done
