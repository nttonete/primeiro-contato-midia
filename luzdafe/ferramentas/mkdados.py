"""Recria historias21_dados.json (texto Bíblia Livre + correções aplicadas no lote de 10/11)."""
import json, re
S = "/home/claude/serie"
T = {}
for line in open(f"{S}/fonte_biblia/blivre.tsv", encoding="utf-8"):
    k, _, t = line.rstrip("\n").partition("\t")
    T[k] = re.sub(r"\bSENHOR\b", "Senhor", t).strip()
# (id, header, gancho, referência, livro, cap, ctx_ini, ctx_fim, hl_ini, hl_fim)
L = [
 ("35_1sm17","1 SAMUEL 17","Um menino, uma pedra e um gigante","1 Samuel 17:48-50","1SA",17,45,51,48,50),
 ("36_mt14","MATEUS 14","Pedro andou sobre as águas","Mateus 14:25-31","MAT",14,22,33,25,31),
 ("37_dn6","DANIEL 6","Uma noite inteira com os leões","Daniel 6:19-22","DAN",6,16,23,19,22),
 ("38_jo11","JOÃO 11","Morto há 4 dias. Até Jesus chamar","João 11:41-44","JHN",11,38,45,41,44),
 ("39_dn3","DANIEL 3","Jogaram 3 no fogo. O rei viu 4","Daniel 3:24-27","DAN",3,19,28,24,27),
 ("40_mc4","MARCOS 4","Jesus dormia no meio da tempestade","Marcos 4:37-41","MRK",4,33,41,37,41),
 ("41_ex14","ÊXODO 14","O dia em que o mar se abriu","Êxodo 14:21-22","EXO",14,15,25,21,22),
 ("42_jo6","JOÃO 6","5 pães e 2 peixes para 5 mil","João 6:9-13","JHN",6,5,14,9,13),
 ("43_js10","JOSUÉ 10","O dia em que o sol parou","Josué 10:12-14","JOS",10,9,15,12,14),
 ("44_lc19","LUCAS 19","Ele subiu numa árvore para ver Jesus","Lucas 19:3-6","LUK",19,1,10,3,6),
 ("45_lc5","LUCAS 5","Uma noite sem peixe. Até Jesus falar","Lucas 5:4-7","LUK",5,1,11,4,7),
 ("46_mc5","MARCOS 5","12 anos doente. Bastou um toque","Marcos 5:25-29","MRK",5,24,34,25,29),
 ("47_1rs18","1 REIS 18","Fogo caiu do céu diante de todos","1 Reis 18:36-39","1KI",18,30,40,36,39),
 ("48_lc23","LUCAS 23","O ladrão que foi com Jesus ao paraíso","Lucas 23:39-43","LUK",23,33,46,39,43),
 ("49_gn8","GÊNESIS 8","A pomba voltou com uma folha no bico","Gênesis 8:8-11","GEN",8,6,13,8,11),
 ("50_at16","ATOS 16","Presos, cantaram à meia-noite","Atos 16:25-26","ACT",16,22,31,25,26),
 ("51_jo2","JOÃO 2","O primeiro milagre de Jesus","João 2:7-10","JHN",2,1,11,7,10),
 ("52_mc12","MARCOS 12","Deu menos que todos. E deu mais","Marcos 12:41-44","MRK",12,38,44,41,44),
 ("53_mc10","MARCOS 10","Mandaram ele calar. Ele gritou mais","Marcos 10:47-52","MRK",10,46,52,47,52),
 ("54_lc22","LUCAS 22","O galo cantou e Jesus olhou para Pedro","Lucas 22:60-62","LUK",22,54,62,60,62),
 ("55_lc15","LUCAS 15","Ele voltou sem nada. O pai correu","Lucas 15:20-24","LUK",15,17,24,20,24),
]
GLOBAL = [("O teus Deus","O teu Deus"),("vinde!Então","vinde! Então"),("parou se secou","se secou"),
          ("consegiu","conseguiu"),("dizes.E","dizes. E"),("de intima","de íntima"),("até encima","até em cima"),
          ("E tu, Lua","e tu, Lua"),("Até tanto","até tanto"),("chegou a aquele","chegou àquele"),("viuisso ,","viu isso,")]
VERSE = {("GEN",8,9):("E não achou","e não achou"),("JHN",2,10):("E disse-lhe","e disse-lhe"),
         ("MRK",10,51):("Jesus, lhe perguntou","Jesus lhe perguntou"),("MRK",10,52):("Jesus, lhe perguntou","Jesus lhe perguntou"),
         ("MRK",12,44):("Porque todos","porque todos")}
out = []
for i, (vid, hdr, hook, ref, bk, ch, a, b, ha, hb) in enumerate(L):
    v = {}
    for n in range(a, b + 1):
        t = T[f"{bk} {ch}:{n}"]
        for x, y in GLOBAL: t = t.replace(x, y)
        if (bk, ch, n) in VERSE: t = t.replace(*VERSE[(bk, ch, n)])
        assert t, (vid, n)
        v[n] = t
    paras = []
    for hl, sel in ((False, [n for n in v if n < ha]), (True, [n for n in v if ha <= n <= hb]), (False, [n for n in v if n > hb])):
        if sel: paras.append(dict(hl=hl, items=[[n, v[n]] for n in sel]))
    out.append(dict(id=vid, hdr=hdr, hook=hook, ref=ref, paras=paras, idx=i))
json.dump(out, open(f"{S}/historias21_dados.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "ok")
