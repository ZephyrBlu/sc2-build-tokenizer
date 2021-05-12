from dataclasses import dataclass


@dataclass
class ParsedBuild:
    race: str
    build: list

    def to_json(self):
        return {
            'race': self.race,
            'build': self.build,
        }


@dataclass
class TokenizedBuild:
    race: str
    tokens: list
    probability: float
    probability_values: list
    information: float
    information_values: list

    def to_json(self):
        return {
            'race': self.race,
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
