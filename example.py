from pathlib import Path
import logging
from difflib import SequenceMatcher
import math
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

        with open('sc2_build_tokenizer/data/parsed_builds.py', 'w', encoding='utf-8') as builds:
            builds.write(f'PARSED_BUILDS = {serialized_builds}')
    else:
        parsed_builds = list(map(
            lambda game: list([
                ParsedBuild(
                    build['race'],
                    build['player'],
                    build['game_length'],
                    build['max_collection_rate'],
                    build['win'],
                    build['build'],
                ) for build in game
            ]),
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
                        build.player,
                        build.max_collection_rate,
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
                        build['player'],
                        build['max_collection_rate'],
                        build['tokens'],
                        build['probability'],
                        build['probability_values'],
                        build['information'],
                        build['information_values'],
                    ) for build in game
                ]),
                TOKENIZED_BUILDS,
            ))

    race2 = 'Zerg'
    race1 = 'Terran'
    MAX_COMPARISON_DIFF = 3
    MIN_MINING_BASES = 3
    matchup = sorted([race1, race2])
    race = race1
    opener = defaultdict(int)
    mu = 0
    macro = 0
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
                # print(build.tokens, '\n')
                opener[tuple(opening_build)] += 1

    # print(f'{mu} games')
    # top_openers = sorted(list(opener.items()), key=lambda o: o[1], reverse=True)
    # for o, c in top_openers:
    #     print(c, o)

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
                mu_builds.append(build)

    filtered_builds = {}
    seen_builds = set()

    for build_id, build in enumerate(mu_builds):
        # less than 2 base
        if build.max_collection_rate < (888 * MIN_MINING_BASES):
            continue

        macro += 1

        for other_id, other in enumerate(mu_builds):
            # same build
            if build_id == other_id:
                continue

            # less than 2 base
            if other.max_collection_rate < (888 * MIN_MINING_BASES):
                continue

            min_build_length = max(build.build[-1][1], other.build[-1][1])
            filtered_build = list(
                map(
                    lambda x: x[0],
                    filter(
                        lambda x: x[1] <= min_build_length and 'Reactor' not in x[0] and 'TechLab' not in x[0],
                        build.build,
                    ),
                )
            )
            filtered_other = list(
                map(
                    lambda x: x[0],
                    filter(
                        lambda x: x[1] <= min_build_length and 'Reactor' not in x[0] and 'TechLab' not in x[0],
                        other.build,
                    ),
                )
            )

            if tuple(filtered_build) not in filtered_builds:
                filtered_builds[(tuple(filtered_build))] = 0

            if filtered_build == filtered_other and other_id not in seen_builds:
                filtered_builds[(tuple(filtered_build))] += 1
                seen_builds.add(other_id)

        seen_builds.add(build_id)

    def compare_builds(build, other):
        s = SequenceMatcher(None, build, other)
        b = s.get_matching_blocks()

        build_matches = []
        other_matches = []
        compare_values = []
        compare_diff = 0

        for match in b:
            for i in range(match.a, match.a + match.size):
                build_matches.append(i)

            for i in range(match.b, match.b + match.size):
                other_matches.append(i)

        comparison_builds = [
            (build, build_matches),
            (other, other_matches),
        ]
        comparison_weight = defaultdict(int)
        for compare_build, compare_matches in comparison_builds:
            compare_missing = {}
            compare_buildings = []
            for index, building in enumerate(compare_build):
                # if non-matching building
                if index not in compare_matches:
                    compare_missing[building] = 0
                    compare_buildings.append((building, index))

            for building in compare_build:
                if building in compare_missing:
                    compare_missing[building] += 1

            for building, index in compare_buildings:
                probability = TOKEN_PROBABILITY[race1][race2][(building,)]
                information = -math.log2(probability)
                tf_idf = (1 / compare_missing[building]) * information
                comparison_weight[building] += tf_idf  # (1 / (index if index != 0 else index + 1)) * 
                compare_diff += tf_idf
                compare_values.append((building, compare_missing[building], round(information, 1), round(tf_idf, 1)))

        return compare_diff, comparison_weight, compare_values, s.ratio()

    build_comparisons = {}
    for build_id, build in enumerate(filtered_builds.keys()):
        for other_id, other in enumerate(filtered_builds.keys()):
            # same build
            if build_id == other_id:
                continue

            compare_diff, comparison_weight, compare_values, ratio = compare_builds(build, other)
            build_comparisons[tuple(sorted([build_id, other_id]))] = compare_diff

    # print('Build Comparisons', len(build_comparisons))
    # for c, b in build_comparisons:
    #     print(c, b)

    build_list = list(filtered_builds.items())
    build_clusters = {}
    for build_id, build in enumerate(build_list):
        build_clusters[build_id] = []

    while True:
        cluster_comparisons = {}
        for (build_id, other_id), diff in build_comparisons.items():
            if build_id in build_clusters and other_id in build_clusters:
                cluster_comparisons[(build_id, other_id)] = diff

        if not cluster_comparisons:
            break

        sorted_comparisons = sorted(
            cluster_comparisons.items(),
            key=lambda build: build[1],
        )

        completed = False
        for min_comparison_builds, min_comparison_diff in sorted_comparisons:
            if min_comparison_diff > MAX_COMPARISON_DIFF:
                break

            # check constituent builds
            cluster_complete_linkage = True
            for build_id in min_comparison_builds:
                other_comparison_id = min_comparison_builds[0] if min_comparison_builds[1] == build_id else min_comparison_builds[1]
                for other_id in build_clusters[build_id]:
                    cross_cluster_diff = build_comparisons[tuple(sorted([other_comparison_id, other_id]))]
                    if cross_cluster_diff > MAX_COMPARISON_DIFF:
                        print(other_comparison_id, other_id, cross_cluster_diff)
                        cluster_complete_linkage = False
                        break

                if not cluster_complete_linkage:
                    break

            if not cluster_complete_linkage:
                continue

            max_build_count = -1
            max_build_id = None
            for build_id in min_comparison_builds:
                if build_list[build_id][1] > max_build_count:
                    max_build_count = build_list[build_id][1]
                    max_build_id = build_id

            other_build_id = min_comparison_builds[0] if min_comparison_builds[1] == max_build_id else min_comparison_builds[1]
            build_clusters[max_build_id].extend(build_clusters[other_build_id])
            build_clusters[max_build_id].append(other_build_id)
            del build_clusters[other_build_id]
            completed = True
            break

        if not completed:
            break

    print('\n')
    all_builds = 0
    cluster_total = 0
    unique_total = 0
    for build_id, clustered in build_clusters.items():
        total = build_list[build_id][1] + 1
        for other_id in clustered:
            total += build_list[other_id][1] + 1
        all_builds += total
        if total >= 3:
            cluster_total += total
        else:
            unique_total += total
        print(build_id, f'(Total: {total})', clustered)
    print(unique_total, cluster_total)
    print(unique_total + cluster_total, all_builds)
    print(cluster_total / all_builds)

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
