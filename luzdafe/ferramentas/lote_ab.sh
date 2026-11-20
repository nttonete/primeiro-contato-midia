#!/bin/sh
# uso: lote_ab.sh id1 id2 ... -> áudio (trilha+voz), ASR na voz, render sincronizado em ab/
cd /home/claude/serie
mkdir -p ab asr_ab
for id in "$@"; do
  python3 bin/montar_audio.py vozes_ab/$id.mp3 ab/$id.m4a asr_ab/$id.wav > logs_ab_$id.txt 2>&1
  python3 asr_words.py asr_ab/$id.wav asr_ab/$id.json > /dev/null
  HOOK_END=3.6 python3 bin/pagina_sync.py lote_ab_dados.json $id ab/$id.m4a asr_ab/$id.json ab/$id.mp4 >> logs_ab_$id.txt 2>&1
done
