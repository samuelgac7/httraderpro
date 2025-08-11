def extract_features_from_player(player):
    def _get(attr, default=None):
        return getattr(player, attr, default)

    name = f"{_get('first_name','') or ''} {_get('last_name','') or ''}".strip() or _get('name', '(Player)')

    feats = {
        "id": int(_get('id', 0)),
        "name": name,
        "age_years": int(getattr(player, 'age', 17)),
        "age_days": int(getattr(player, 'age_days', 0)),
        "playmaking": int(getattr(player, 'playmaking', 0)),
        "passing": int(getattr(player, 'passing', 0)),
        "defending": int(getattr(player, 'defending', 0)),
        "scoring": int(getattr(player, 'scoring', 0)),
        "winger": int(getattr(player, 'winger', 0)),
        "goalkeeping": int(getattr(player, 'goalkeeping', 0)),
        "set_pieces": int(getattr(player, 'set_pieces', 0)),
        "stamina": int(getattr(player, 'stamina', 0)),
        "tsi": int(getattr(player, 'tsi', 0)),
        "form": int(getattr(player, 'form', 0)),
        "experience": int(getattr(player, 'experience', 0)),
        "specialty_index": int(getattr(player, 'specialty', 0) or 0),
        "specialty": None,
    }
    idx_to_name = {0:"None",1:"Technical",2:"Quick",3:"Unpredictable",4:"Powerful",5:"Head"}
    feats["specialty"] = idx_to_name.get(feats["specialty_index"], "None")
    return feats
