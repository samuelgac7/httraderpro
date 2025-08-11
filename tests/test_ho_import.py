from ho_import import parse_ho_paste, parse_ho_csv, ho_specialty_to_index

def test_parse_ho_paste_basic():
    txt = "Nombre: Test\nEdad: 17 años y 7 días\nPlaymaking: 7\nPases: 5\nDefensa: 4\nExtremo: 4\nAnotación: 3\nForma: 6\nTSI: 1200\nExperiencia: 2\nEspecialidad: Rápido"
    row = parse_ho_paste(txt)
    assert row["AgeYears"] == 17
    assert row["AgeDays"] >= 0
    assert row["Playmaking"] == 7
    assert ho_specialty_to_index("Rápido") == 2


def test_parse_ho_paste_goalkeeper():
    txt = (
        "Nombre: GK\nEdad: 19 años y 0 días\nPortero: 8\n"
        "Balón parado: 6\nForma: 5\nTSI: 3000\nExperiencia: 2"
    )
    row = parse_ho_paste(txt)
    assert row["Goalkeeping"] == 8
    assert row["SetPieces"] == 6


def test_parse_ho_csv_goalkeeper():
    import pathlib

    csv_path = pathlib.Path(__file__).parent / "data" / "goalkeeper_ho.csv"
    df = parse_ho_csv(csv_path.read_text())
    row = df.iloc[0]
    assert row["Goalkeeping"] == 8
    assert row["SetPieces"] == 6
