import sys; sys.path.insert(0, sys.path[0])
from textfix import run
E = [
 (34, "Il rituale Thailandese", "Il rituale thailandese"),
 (3, "Il rituale Thailandese", "Il rituale thailandese"),
 (68, "un messaggio", "un massaggio"),
 (29, "che, negli ultimi anni, è uscito", "che, negli ultimi anni, sono usciti"),
 (29, "sul qi e", "sul Qi e"),
 (32, "chi lo esegue", "chi la esegue"),
 (33, "che il corpo resiste", "a cui il corpo resiste"),
 (35, "chi lo ha ricevuto", "chi l’ha ricevuta"),
 (35, "Chi lo riceve in silenzio", "Chi la riceve in silenzio"),
 (45, "in modo che si riesce", "in un modo che si riesca"),
 (52, "In Occidente contemporaneo", "Nell’Occidente contemporaneo"),
 (57, "Il muscolo orbitale", "Il muscolo orbicolare"),
 (60, "gangli del collo", "linfonodi del collo"),
 (78, "tiarè", "tiaré"),
 (81, "sui temporali", "sulle tempie"),
 (84, "senza che l’abbiate deciso voi", "senza che tu l’abbia deciso"),
 (90, "si porta presenza", "si portano presenza"),
 (96, "non si è ancora concessa", "non si concedono ancora"),
 (96, "non si è ancora permessa", "non si permettono ancora"),
 (100, "mi ha cambiato sia", "mi ha cambiata sia"),
]
run(sys.argv[1], sys.argv[2], edits=E, report=sys.argv[3])
