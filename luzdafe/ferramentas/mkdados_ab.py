"""Lote A/B (22/11-29/11): 15 versículos curtos + 7 histórias curtas. Texto Bíblia Livre."""
import json, re
S = "/home/claude/serie"
T = {}
for line in open(f"{S}/fonte_biblia/blivre.tsv", encoding="utf-8"):
    k, _, t = line.rstrip("\n").partition("\t")
    T[k] = re.sub(r"\bSENHOR\b", "Senhor", t).strip()
FIX = [("e sava os","e salva os"),("eles ,e lhes","eles, e lhes"),("nem a chamas","nem as chamas"),("criatura é ;","criatura é;"),
       ("dá- la","dá-la"),("Jesus , movido","Jesus, movido"),("isto , maravilhou","isto, maravilhou")]
# (id, tipo, header, gancho, ref, livro, cap, hl_ini, hl_fim)
L = [
 ("56_sl34","V","SALMOS 34","Para quem está de coração partido","Salmos 34:18","PSA",34,18,18),
 ("57_mt19","V","MATEUS 19","O que parece impossível pra você?","Mateus 19:26","MAT",19,26,26),
 ("58_js6","H","JOSUÉ 6","Gritaram, e a muralha caiu","Josué 6:20","JOS",6,20,20),
 ("59_sl30","V","SALMOS 30","O choro passa. A alegria vem","Salmos 30:5","PSA",30,5,5),
 ("60_is43","V","ISAÍAS 43","Deus atravessa o fogo com você","Isaías 43:2","ISA",43,2,2),
 ("61_jo8","H","JOÃO 8","Ninguém a condenou. Nem Jesus","João 8:10-11","JHN",8,10,11),
 ("62_rm8","V","ROMANOS 8","Nada na sua vida é por acaso","Romanos 8:28","ROM",8,28,28),
 ("63_fp4","V","FILIPENSES 4","Você consegue. Leia isto","Filipenses 4:13","PHP",4,13,13),
 ("64_mc1","H","MARCOS 1","Ele tocou em quem ninguém tocava","Marcos 1:40-42","MRK",1,40,42),
 ("65_sf3","V","SOFONIAS 3","Deus se alegra por você","Sofonias 3:17","ZEP",3,17,17),
 ("66_ex14","V","ÊXODO 14","Deus luta por você","Êxodo 14:14","EXO",14,14,14),
 ("67_mt28","H","MATEUS 28","O túmulo estava vazio","Mateus 28:5-6","MAT",28,5,6),
 ("68_jo16","V","JOÃO 16","Jesus avisou: vai ter aflição","João 16:33","JHN",16,33,33),
 ("69_sl56","V","SALMOS 56","Para o dia em que bater o medo","Salmos 56:3","PSA",56,3,3),
 ("70_rt1","H","RUTE 1","A promessa mais fiel da Bíblia","Rute 1:16","RUT",1,16,16),
 ("71_dt31","V","DEUTERONÔMIO 31","Deus já está lá na frente","Deuteronômio 31:8","DEU",31,8,8),
 ("72_2co5","V","2 CORÍNTIOS 5","Seu passado não te define","2 Coríntios 5:17","2CO",5,17,17),
 ("73_jo20","H","JOÃO 20","Tomé duvidou. Até tocar","João 20:27-28","JHN",20,27,28),
 ("74_sl27","V","SALMOS 27","A quem temerei?","Salmos 27:1","PSA",27,1,1),
 ("75_jo14","V","JOÃO 14","A paz que o mundo não dá","João 14:27","JHN",14,27,27),
 ("76_ex3","H","ÊXODO 3","Uma sarça em fogo que não queimava","Êxodo 3:2-4","EXO",3,2,4),
 ("77_pv16","V","PROVÉRBIOS 16","Antes de começar, leia isto","Provérbios 16:3","PRO",16,3,3),
]
out = []
for i, (vid, tipo, hdr, hook, ref, bk, ch, ha, hb) in enumerate(L):
    v = {}
    for n in range(ha - 4, hb + 4):
        t = T.get(f"{bk} {ch}:{n}", "")
        if not t: continue
        for x, y in FIX: t = t.replace(x, y)
        v[n] = t
    paras = []
    for hl, sel in ((False, [n for n in v if n < ha]), (True, [n for n in v if ha <= n <= hb]), (False, [n for n in v if n > hb])):
        if sel: paras.append(dict(hl=hl, items=[[n, v[n]] for n in sel]))
    narr = " ".join(v[n] for n in range(ha, hb + 1))
    out.append(dict(id=vid, tipo=tipo, hdr=hdr, hook=hook, ref=ref, paras=paras, idx=i, narr=narr))
json.dump(out, open(f"{S}/lote_ab_dados.json", "w"), ensure_ascii=False, indent=1)
for d in out: print(d["id"], len(d["narr"]), "|", d["narr"])
