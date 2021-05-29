from dataclasses import dataclass


@dataclass
class ParsedBuild:
    race: str
    player: str
    game_map: str
    game_length: int
    max_collection_rate: int
    win: bool
    build: list

    def to_json(self):
        return {
            'race': self.race,
            'player': self.player,
            'game_map': self.game_map,
            'game_length': self.game_length,
            'max_collection_rate': self.max_collection_rate,
            'win': self.win,
            'build': self.build,
        }


@dataclass
class TokenizedBuild:
    race: str
    player: str
    max_collection_rate: int
    tokens: list
    probability: float
    probability_values: list
    information: float
    information_values: list

    def to_json(self):
        return {
            'race': self.race,
            'player': self.player,
            'max_collection_rate': self.max_collection_rate,
            'tokens': self.tokens,
            'probability': self.probability,
            'probability_values': self.probability_values,
            'information': self.information,
            'information_values': self.information_values,
        }


@dataclass
class TokenDistributions:
    probability: dict
    information: dict

    @staticmethod
    def to_dict(distribution):
        for k, v in distribution.items():
            if isinstance(v, dict):
                distribution[k] = TokenDistributions.to_dict(v)
        return dict(distribution)
