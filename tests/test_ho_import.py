from ho_import import parse_ho_paste, ho_specialty_to_index

def test_parse_ho_paste_basic():
    txt = "Nombre: Test\nEdad: 17 años y 7 días\nPlaymaking: 7\nPases: 5\nDefensa: 4\nExtremo: 4\nAnotación: 3\nForma: 6\nTSI: 1200\nExperiencia: 2\nEspecialidad: Rápido"
    row = parse_ho_paste(txt)
    assert row["AgeYears"] == 17
    assert row["AgeDays"] >= 0
    assert row["Playmaking"] == 7
    assert ho_specialty_to_index("Rápido") == 2
