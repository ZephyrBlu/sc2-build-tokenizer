import copy
import math
from collections import defaultdict

from sc2_build_tokenizer.dataclasses import (
    TokenizedBuild,
    TokenDistributions,
)
from sc2_build_tokenizer.data import TOKEN_INFORMATION
from sc2_build_tokenizer.data import TOKEN_PROBABILITY


def generate_build_tokens(build, source=None):
    build_tokens = source
    if not source:
        build_tokens = defaultdict(int)

    for i in range(0, len(build)):
        for index in range(1, 9):
            token = build[i:i + index]
            build_tokens[tuple(token)] += 1

            # exit if we're at the end of the build
            if i + index >= len(build):
                break

    return build_tokens


def generate_token_distributions(source):
    distributions = TokenDistributions({}, {})
    tokenized = list(source.items())
    unigrams = {}
    ngram_tokens = defaultdict(dict)

    # unigrams are a special case because they have no corresponding
    # predicted token. It's easier to store them separately
    for tokens, count in tokenized:
        if len(tokens) == 1:
            unigrams[tokens] = count
            continue

        ngram = tokens[:-1]
        predicted = tokens[-1]

        ngram_tokens[ngram][predicted] = count

    total = sum(unigrams.values())
    tokens = list(unigrams.items())
    for token, count in tokens:
        distributions.probability[token] = count / total
        distributions.information[token] = -math.log2(count / total)
        print(count, distributions.probability[token], token)

    for tokens, outcomes in ngram_tokens.items():
        total = sum(outcomes.values())

        # 10 is an arbitrary minimum number of samples
        # to reduce overfitting paths based on a few samples
        if total < 10:
            continue

        predicted = list(outcomes.items())
        print(tokens)
        for token, count in predicted:
            distributions.probability[(*tokens, token)] = count / total
            distributions.information[(*tokens, token)] = -math.log2(count / total)
            print(count, distributions.probability[(*tokens, token)], token)
        print('\n')

    return distributions


def _generate_next_tokens(
    build,
    *,
    max_token_size=8,
    build_index=0,
    build_tokens=[],
    probability=1,
    probability_values=[],
    information=0,
    information_values=[],
    token_probability,
    token_information,
):
    build_length = len(build)
    all_paths = []
    # generate new path information for each possible new token
    for i in range(1, max_token_size + 1):
        # don't need copies for values, but it keeps things explicit
        updated_tokens = copy.deepcopy(build_tokens)
        updated_probability = copy.deepcopy(probability)
        updated_probability_values = copy.deepcopy(probability_values)
        updated_information = copy.deepcopy(information)
        updated_information_values = copy.deepcopy(information_values)

        token = tuple(build[build_index:build_index + i])

        # if we don't have a record of the preceding sequence,
        # it was too unlikely to record so we bail
        if token not in token_probability:
            continue

        token_prob = 1
        # print(token, len(token))
        for index in range(0, len(token)):
            token_fragment = token[:index + 1]
            token_prob *= token_probability[token_fragment]
            updated_probability_values.append(
                token_probability[token_fragment]
            )
            updated_information += token_information[token_fragment]
            updated_information_values.append(
                token_information[token_fragment]
            )
            # print(
            #     index + 1,
            #     TOKEN_PROBABILITY[player_race][opp_race][token_fragment],
            #     token_prob,
            #     token_fragment,
            # )
        # print('\n')
        updated_probability *= token_prob
        updated_tokens.append(token)

        # exit if we're at the end of the build
        if build_index + i >= build_length:
            # print(new_path, token, build_index, i, build_index + i)
            all_paths.append(TokenizedBuild(
                updated_tokens,
                updated_probability,
                updated_probability_values,
                updated_information,
                updated_information_values,
            ))
            return all_paths

        calculated_paths = _generate_next_tokens(
            build,
            build_index=build_index + i,
            build_tokens=updated_tokens,
            probability=updated_probability,
            probability_values=updated_probability_values,
            information=updated_information,
            information_values=updated_information_values,
            token_probability=token_probability,
            token_information=token_information
        )
        all_paths.extend(calculated_paths)
    return all_paths


def generate_token_paths(
    build,
    player_race,
    opp_race,
    token_probability=TOKEN_PROBABILITY,
    token_information=TOKEN_INFORMATION,
):
    if player_race and opp_race:
        if (
            player_race in token_probability
            and opp_race in token_probability[player_race]
        ):
            token_probability = token_probability[player_race][opp_race]

        if (
            player_race in token_information
            and opp_race in token_information[player_race]
        ):
            token_information = token_information[player_race][opp_race]

    # print(token_probability, token_information)

    paths = _generate_next_tokens(
        build,
        token_probability=token_probability,
        token_information=token_information,
    )

    # sort by overall conditional probability of path
    paths.sort(key=lambda path: path.probability, reverse=True)
    return paths
