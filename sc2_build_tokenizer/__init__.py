from sc2_build_tokenizer.parse import parse_builds
from sc2_build_tokenizer.tokenize import (
    generate_build_tokens,
    generate_token_distributions,
    generate_token_paths,
)
from sc2_build_tokenizer.dataclasses import (
    ParsedBuild,
    TokenizedBuild,
    TokenizedDistributions,
)


def tokenize(replay):
    builds = parse_builds(replay)

    for build in builds:
        races = []
        for player_build in build:
            races.append(build.race)

        tokenized = []
        for player_build in build:
            player_race = build.race
            opp_race = races[0] if races[1] == player_race else races[1]
            paths = generate_token_paths(player_build, player_race, opp_race)

            # only take the most likely path
            tokenized.append(paths[0])

    return tokenized
