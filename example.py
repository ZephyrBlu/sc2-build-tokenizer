from pathlib import Path
import logging
from collections import defaultdict

from sc2_build_tokenizer import (
    extract_builds,
    generate_build_tokens,
    generate_token_distributions,
    generate_token_paths,
)
from sc2_build_tokenizer.dataclasses import ParsedBuild, TokenizedBuild
from sc2_build_tokenizer.data import PARSED_BUILDS, TOKENIZED_BUILDS

TEST_REPLAY_PATH = Path('replays/IEM/1 - Playoffs/Finals/Reynor vs Zest/20210228 - GAME 1 - Reynor vs Zest - Z vs P - Oxide LE.SC2Replay')
REPLAY_PATH = Path('replays')

BUILD_TOKENS = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
TOKEN_PROBABILITY = defaultdict(lambda: defaultdict(dict))
TOKEN_INFORMATION = defaultdict(lambda: defaultdict(dict))

# logging.basicConfig(level=logging.INFO)


def to_dict(struct):
    for k, v in struct.items():
        if isinstance(v, dict):
            struct[k] = to_dict(v)
    return dict(struct)


def manual_tokenize(
    *,
    _test=False,
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

    if not _test:
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

    if not _test:
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

    if not _test:
        if _write_tokenized:
            tokenized_builds = []
            print(f'{len(parsed_builds)} Games')
            for count, game in enumerate(parsed_builds):
                races = []
                for build in game:
                    races.append(build.race)
                races.sort()

                game_builds = []
                for build in game:
                    if not build.build:
                        continue

                    opp_race = races[0] if races[1] == build.race else races[1]

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

            serialized_tokenized_builds = list(map(
                lambda game: list([tokenized_build.to_json() for tokenized_build in game]),
                tokenized_builds,
            ))
            print(f'Serialized Tokenized Builds: {len(serialized_tokenized_builds)}')
            with open('sc2_build_tokenizer/data/tokenized_builds.py', 'w') as tokenized:
                tokenized.write(f'TOKENIZED_BUILDS = {serialized_tokenized_builds}')
        else:
            tokenized_builds = list(map(
                lambda game: list([
                    TokenizedBuild(
                        build['race'],
                        build['tokens'],
                        build['probability'],
                        build['probability_values'],
                        build['information'],
                        build['information_values'],
                    ) for build in game
                ]),
                TOKENIZED_BUILDS,
            ))

    matchup = sorted(['Protoss', 'Terran'])
    race = 'Terran'
    opener = defaultdict(int)
    mu = 0
    for game in tokenized_builds:
        races = []
        for build in game:
            races.append(build.race)
        races.sort()

        if races != matchup:
            continue

        mu += 1

        for build in game:
            if build.race == race:
                opening_build = []
                mid_build = []
                build_index = 0
                total_buildings = 0
                o_b = 0
                while total_buildings < 4 and build_index < len(build.tokens):
                    if o_b < 4:
                        opening_build.append(build.tokens[build_index])
                        o_b += len(build.tokens[build_index])
                    else:
                        mid_build.append(build.tokens[build_index])
                        total_buildings += len(build.tokens[build_index])
                    build_index += 1
                print(build.tokens, '\n')
                opener[tuple(opening_build)] += 1

    print(f'{mu} games')
    top_openers = sorted(list(opener.items()), key=lambda o: o[1], reverse=True)
    for o, c in top_openers:
        print(c, o)

    mu_builds = []
    for game in parsed_builds:
        races = []
        for build in game:
            races.append(build.race)
        races.sort()

        if races != matchup:
            continue

        for build in game:
            if build.race == race:
                mu_builds.append(build.build)

    from difflib import SequenceMatcher
    for build in mu_builds:
        for other in mu_builds:
            s = SequenceMatcher(None, build, other)
            b = s.get_matching_blocks()

            build_matches = []
            other_matches = []
            for match in b:
                for i in range(match.a, match.a + match.size):
                    build_matches.append(i)

                for i in range(match.b, match.b + match.size):
                    other_matches.append(i)

            for index, building in enumerate(build):
                # if non-matching building
                if index not in build_matches:
                    # calculate tf-idf and add to total
                    # tf = building count in current build
                    # idf = fraction of builds containing building
                    # OR
                    # idf = building frequency over all builds
                    pass

            print(s.ratio())
            print(build_matches)
            print(other_matches)
            print(b)
            print(build)
            print(other)
            print('\n')
        break

    # ----------------------
    # tokenized test replay
    # ----------------------

    if _test:
        test_builds = extract_builds(TEST_REPLAY_PATH)[0]
        races = []
        for build in test_builds:
            races.append(build.race)

        print('Test Builds', test_builds, '\n')

        for build in test_builds:
            opp_race = races[0] if build.race == races[1] else races[1]
            paths = generate_token_paths(
                build.build,
                build.race,
                opp_race,
            )

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

            # optimal_path = paths[0]
            # print(
            #     optimal_path.information,
            #     optimal_path.probability,
            #     optimal_path.tokens,
            #     optimal_path.information_values,
            #     optimal_path.probability_values,
            #     '\n',
            # )

            print(build)
            print(paths[0])


# import cProfile
# import re
# cProfile.run('''
manual_tokenize(
    _test=False,
    _write_builds=False,
    _write_distributions=False,
    _write_tokenized=False,
)
# ''', 'restats')

# import pstats
# from pstats import SortKey
# p = pstats.Stats('restats')
# p.strip_dirs().sort_stats(SortKey.CUMULATIVE).print_stats()
