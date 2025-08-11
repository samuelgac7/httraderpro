import io
import re
import pandas as pd

SPECIALTY_MAP = {
    "None":"None","Ninguna":"None","No":"None",
    "Technical":"Technical","Técnico":"Technical",
    "Quick":"Quick","Rápido":"Quick",
    "Unpredictable":"Unpredictable","Impredecible":"Unpredictable",
    "Powerful":"Powerful","Potente":"Powerful",
    "Head":"Head","Head Specialist":"Head","Cabezazo":"Head",
}

def ho_specialty_to_index(name:str)->int:
    name = (name or "None").strip()
    name = SPECIALTY_MAP.get(name, name)
    return {"None":0,"Technical":1,"Quick":2,"Unpredictable":3,"Powerful":4,"Head":5}.get(name,0)

def _to_int(x, default=0):
    try:
        return int(str(x).strip())
    except:
        try:
            return int(float(str(x).replace(",",".")))
        except:
            return default

def parse_ho_csv(text:str):
    for sep in [",",";","\t","|"]:
        try:
            df = pd.read_csv(io.StringIO(text), sep=sep)
            if df.shape[1] < 3:
                continue
            break
        except Exception:
            df = None
    if df is None:
        return pd.DataFrame()

    cols = {c.strip():c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in cols: return cols[n]
            for k in cols:
                if k.lower()==n.lower(): return cols[k]
        return None

    name_c = pick("Name","Jugador","Nombre")
    age_c = pick("Age","Edad")
    age_days_c = pick("AgeDays","EdadDías","EdadDias","Days")
    tsi_c = pick("TSI","tsi")
    form_c = pick("Form","Forma")
    exp_c = pick("Experience","Experiencia")
    spec_c = pick("Specialty","Especialidad","Speciality")

    pm_c = pick("Playmaking","Jugadas")
    pas_c = pick("Passing","Pases")
    def_c = pick("Defending","Defensa")
    sco_c = pick("Scoring","Anotación","Anotacion")
    win_c = pick("Winger","Extremo")
    sta_c = pick("Stamina","Resistencia")

    out = []
    for _, r in df.iterrows():
        name = str(r.get(name_c,"Player"))
        ay = int(r.get(age_c,17)) if age_c else 17
        ad = int(r.get(age_days_c,0)) if age_days_c else 0

        out.append({
            "Name": name,
            "AgeYears": ay,
            "AgeDays": ad,
            "TSI": _to_int(r.get(tsi_c,0)),
            "Form": _to_int(r.get(form_c,0)),
            "Experience": _to_int(r.get(exp_c,0)),
            "Specialty": str(r.get(spec_c,"None")) if spec_c else "None",
            "Playmaking": _to_int(r.get(pm_c,0)),
            "Passing": _to_int(r.get(pas_c,0)),
            "Defending": _to_int(r.get(def_c,0)),
            "Scoring": _to_int(r.get(sco_c,0)),
            "Winger": _to_int(r.get(win_c,0)),
            "Stamina": _to_int(r.get(sta_c,0)),
        })
    return pd.DataFrame(out)

def parse_ho_paste(text:str):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    data = {}
    for line in lines:
        if ":" in line:
            k, v = line.split(":",1)
            data[k.strip().lower()] = v.strip()

    def get_num(key, default=0):
        for variant in [key, key.capitalize(), key.upper()]:
            for k in data:
                if k.startswith(variant.lower()):
                    m = re.search(r'(\d+)', data[k])
                    if m: return int(m.group(1))
        return default

    def get_text(key, default=""):
        for k in data:
            if k.startswith(key.lower()):
                return data[k]
        return default

    age_y = get_num("edad", get_num("age",17))
    days = 0
    for k in data:
        if "día" in k or "day" in k:
            m = re.search(r'(\d+)', data[k])
            if m:
                days = int(m.group(1)); break
    if days == 0:
        for k in ["edad","age"]:
            if k in data:
                m = re.search(r'(\d+)\D+(\d+)\D*$', data[k])
                if m:
                    days = int(m.group(2)); break

    spec = get_text("especial", get_text("special", "None"))

    return {
        "Name": get_text("nombre", get_text("name","(Player)")),
        "AgeYears": age_y or 17,
        "AgeDays": days,
        "TSI": get_num("tsi",0),
        "Form": get_num("forma", get_num("form",0)),
        "Experience": get_num("experiencia", get_num("experience",0)),
        "Specialty": spec,
        "Playmaking": get_num("jugadas", get_num("playmaking",0)),
        "Passing": get_num("pases", get_num("passing",0)),
        "Defending": get_num("defensa", get_num("defending",0)),
        "Scoring": get_num("anotación", get_num("anotacion", get_num("scoring",0))),
        "Winger": get_num("extremo", get_num("winger",0)),
        "Stamina": get_num("resistencia", get_num("stamina",0)),
    }
