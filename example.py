from pathlib import Path
import logging
from collections import defaultdict

from sc2_build_tokenizer import (
    extract_builds,
    generate_build_tokens,
    generate_token_distributions,
    generate_token_paths,
)
from sc2_build_tokenizer.dataclasses import ParsedBuild
from sc2_build_tokenizer.data import PARSED_BUILDS

TEST_REPLAY_PATH = Path('IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 1 - Reynor vs Zest - Z vs P - Oxide LE.SC2Replay')
REPLAY_PATH = Path('IEM')

BUILD_TOKENS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
TOKEN_PROBABILITY = defaultdict(lambda: defaultdict(dict))
TOKEN_INFORMATION = defaultdict(lambda: defaultdict(dict))

logging.basicConfig(level=logging.CRITICAL)


def to_dict(struct):
    for k, v in struct.items():
        if isinstance(v, dict):
            struct[k] = to_dict(v)
    return dict(struct)


def manual_tokenize(
    *,
    _write_builds=False,
    _write_distributions=True,
    _write_tokenized=True,
):
    if _write_builds:
        parsed_builds = extract_builds(REPLAY_PATH)
        serialized_builds = list(map(
            lambda game: list([build.to_json() for build in game]),
            parsed_builds,
        ))

        with open('sc2_build_tokenizer/data/parsed_builds.py', 'w') as builds:
            builds.write(f'PARSED_BUILDS = {serialized_builds}')
    else:
        parsed_builds = list(map(
            lambda game: list([ParsedBuild(build['race'], build['build']) for build in game]),
            PARSED_BUILDS,
        ))

    # ----------------------
    # generate build tokens
    # ----------------------

    for build in parsed_builds:
        races = []
        for player_build in build:
            races.append(player_build.race)

        for player_build in build:
            player_race = player_build.race
            opp_race = races[0] if races[1] == player_race else races[1]
            BUILD_TOKENS[player_race][opp_race] = generate_build_tokens(
                player_build.build,
                BUILD_TOKENS[player_race][opp_race],
            )

    # -----------------------------
    # generate token distributions
    # -----------------------------

    for player_race, other_races in BUILD_TOKENS.items():
        for opp_race, chain in other_races.items():
            distributions = generate_token_distributions(chain)
            TOKEN_PROBABILITY[player_race][opp_race] = distributions.probability
            TOKEN_INFORMATION[player_race][opp_race] = distributions.information

    if _write_distributions:
        with open('sc2_build_tokenizer/data/token_probability.py', 'w') as probabilities:
            probabilities.write(f'TOKEN_PROBABILITY = {to_dict(TOKEN_PROBABILITY)}')

        with open('sc2_build_tokenizer/data/token_information.py', 'w') as information:
            information.write(f'TOKEN_INFORMATION = {to_dict(TOKEN_INFORMATION)}')

    # ---------------------
    # generate token paths
    # ---------------------

    tokenized_builds = []
    print(f'{len(parsed_builds)} Games')
    for count, game in enumerate(parsed_builds):
        game_builds = []
        for build in game:
            paths = generate_token_paths(
                build.build,
                build.race,
                opp_race,
                TOKEN_PROBABILITY,
                TOKEN_INFORMATION,
            )
            optimal_path = paths[0]
            game_builds.append(optimal_path)
        tokenized_builds.append(game_builds)
        print(f'Completed game {count + 1}')

    if _write_tokenized:
        serialized_tokenized_builds = list(map(
            lambda game: list([tokenized_build.to_json() for tokenized_build in game]),
            tokenized_builds,
        ))
        with open('sc2_build_tokenizer/data/tokenized_builds.py', 'w') as tokenized:
            tokenized.write(f'TOKENIZED_BUILDS = {serialized_tokenized_builds}')

    # ----------------------
    # tokenized test replay
    # ----------------------

    # test_builds = extract_builds(TEST_REPLAY_PATH)[0]
    # races = []
    # for build in test_builds:
    #     races.append(build.race)

    # print('Test Builds', test_builds, '\n')

    # for build in test_builds:
    #     opp_race = races[0] if build.race == races[1] else races[1]
    #     paths = generate_token_paths(
    #         build.build,
    #         build.race,
    #         opp_race,
    #         TOKEN_PROBABILITY,
    #         TOKEN_INFORMATION,
    #     )

        # for tokenized_build in paths:
        #     print(
        #         tokenized_build.information,
        #         tokenized_build.probability,
        #         tokenized_build.tokens,
        #         tokenized_build.information_values,
        #         tokenized_build.probability_values,
        #         '\n',
        #     )
        # print(build, '\n\n')


# import cProfile
# import re
# cProfile.run('''
manual_tokenize(
    _write_builds=False,
    _write_distributions=False,
    _write_tokenized=True,
)
# ''', 'restats')

# import pstats
# from pstats import SortKey
# p = pstats.Stats('restats')
# p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()
