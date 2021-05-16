import copy
import math
import logging
from collections import defaultdict

from sc2_build_tokenizer.dataclasses import (
    TokenizedBuild,
    TokenDistributions,
)
from sc2_build_tokenizer.data import TOKEN_PROBABILITY
from sc2_build_tokenizer.data import TOKEN_INFORMATION

CACHED_TOKEN_PROBABILITY = {}
CACHED_TOKEN_INFORMATION = {}

CACHED_PROBABILITY_VALUES = {}
CACHED_INFORMATION_VALUES = {}

logger = logging.getLogger(__name__)


def generate_build_tokens(build, source=None):
    logger.info('Generating tokens from parsed build')

    build_tokens = source
    buildings = list(map(lambda x: x[0], build))
    if not source:
        logger.info('No source supplied, recording token counts locally')
        build_tokens = defaultdict(int)

    logger.info('Iterating through build')
    for i in range(0, len(buildings)):
        logger.debug(f'Generating tokens for {buildings[i]} (Index: {i})')
        for index in range(1, 9):
            token = tuple(buildings[i:i + index])
            logger.debug(f'Found token: {token}')

            build_tokens[token] += 1
            logger.debug(f'Incrementing token count to {build_tokens[token]}')

            # exit if we're at the end of the build
            if i + index >= len(buildings):
                logger.debug('Reached end of build')
                break

    logger.info('Completed generating build tokens')

    return build_tokens


def generate_token_distributions(source):
    logging.info('Generating token distributions from token counts')

    distributions = TokenDistributions({}, {})
    tokenized = list(source.items())
    unigrams = {}
    ngram_tokens = defaultdict(dict)

    # unigrams are a special case because they have no corresponding
    # predicted token. It's easier to store them separately
    logger.info('Iterating through generated tokens')
    for token, count in tokenized:
        if len(token) == 1:
            unigrams[token] = count
            logger.debug(f'Setting unigram token {token} to {count}')
            continue

        ngram = token[:-1]
        predicted = token[-1]

        ngram_tokens[ngram][predicted] = count
        logger.debug(f'Setting ngram token {token} to {count}')

    logger.info('Calculating probabilities and information content for unigram tokens')

    total = sum(unigrams.values())
    unigram_tokens = list(unigrams.items())
    for token, count in unigram_tokens:
        distributions.probability[token] = count / total
        distributions.information[token] = -math.log2(count / total)
        logger.debug(
            count,
            distributions.probability[token],
            distributions.information[token],
            token,
        )

    logger.info('Calculating probabilities and information content for ngram tokens')

    for token, outcomes in ngram_tokens.items():
        logger.debug(f'Calculating for ngram token: {token}')

        total = sum(outcomes.values())

        # 10 is an arbitrary minimum number of samples
        # to reduce overfitting paths based on a few samples
        if total < 10:
            logger.debug(f'Insufficient occurences of token {token}: {total}')
            continue

        predicted = list(outcomes.items())
        for predicted_token, count in predicted:
            logger.debug(f'{count} occurences of {predicted_token}')
            logger.debug(f'Calculating probability of {predicted_token} given token')

            distributions.probability[(*token, predicted_token)] = count / total
            distributions.information[(*token, predicted_token)] = -math.log2(count / total)

            logger.debug(
                f'Distributions for token {(*token, predicted_token)} ({count})',
                distributions.probability[(*token, predicted_token)],
                distributions.information[(*token, predicted_token)],
            )

    logger.info('Completed generating token distributions')

    return distributions


def _generate_next_tokens(
    race,
    player,
    max_collection_rate,
    build,
    *,
    max_token_size=4,
    build_index=0,
    build_tokens=[],
    probability=1,
    probability_values=[],
    information=0,
    information_values=[],
    token_probability,
    token_information,
):
    all_paths = []
    # generate new path information for each possible new token
    for i in range(1, max_token_size + 1):
        updated_tokens = copy.copy(build_tokens)
        updated_probability = probability
        updated_probability_values = copy.copy(probability_values)
        updated_information = information
        updated_information_values = copy.copy(information_values)

        token = tuple(build[build_index:build_index + i])

        logger.info(f'Generated new token of length {i} at index {build_index}: {token}')

        # if we don't have a record of the preceding sequence,
        # it was too unlikely to record so we bail
        if token not in token_probability:
            logger.debug(f'Token probability not found: {token}')
            continue

        fragment_probability = 1
        fragment_information = 0

        fragment_probability_values = []
        fragment_information_values = []

        # start from full token and work backwards looking for cache hit
        for index in range(len(token), 0, -1):
            logger.info(f'At index {index} in token sequence')

            token_fragment = token[:index]
            logger.info(f'Current token fragment: {token_fragment}')

            if (
                token_fragment in CACHED_TOKEN_PROBABILITY
                and token_fragment in CACHED_TOKEN_INFORMATION
            ):
                fragment_probability *= CACHED_TOKEN_PROBABILITY[token_fragment]
                fragment_information += CACHED_TOKEN_INFORMATION[token_fragment]

                fragment_probability_values.extend(CACHED_PROBABILITY_VALUES[token_fragment])
                fragment_information_values.extend(CACHED_INFORMATION_VALUES[token_fragment])
                break

            fragment_probability *= token_probability[token_fragment]
            fragment_probability_values.append(
                token_probability[token_fragment]
            )

            fragment_information += token_information[token_fragment]
            fragment_information_values.append(
                token_information[token_fragment]
            )

        if (
            token not in CACHED_TOKEN_PROBABILITY
            or token not in CACHED_TOKEN_INFORMATION
        ):
            CACHED_TOKEN_PROBABILITY[token] = fragment_probability
            CACHED_TOKEN_INFORMATION[token] = fragment_information

        if (
            token not in CACHED_PROBABILITY_VALUES
            or token not in CACHED_INFORMATION_VALUES
        ):
            CACHED_PROBABILITY_VALUES[token] = fragment_probability_values[::-1]
            CACHED_INFORMATION_VALUES[token] = fragment_information_values[::-1]

        updated_probability *= fragment_probability
        updated_information += fragment_information

        updated_probability_values.extend(fragment_probability_values[::-1])
        updated_information_values.extend(fragment_information_values[::-1])

        updated_tokens.append(token)

        # exit if we're at the end of the build
        if build_index + i >= len(build):
            all_paths.append(TokenizedBuild(
                race,
                player,
                max_collection_rate,
                updated_tokens,
                updated_probability,
                updated_probability_values,
                updated_information,
                updated_information_values,
            ))
            break

        calculated_paths = _generate_next_tokens(
            race,
            player,
            max_collection_rate,
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
    player_name,
    max_collection_rate,
    token_probability=TOKEN_PROBABILITY,
    token_information=TOKEN_INFORMATION,
):
    logger.info(f'Recursively generating all possible token paths for build: {build}')

    if player_race and opp_race:
        if (
            player_race in token_probability
            and opp_race in token_probability[player_race]
        ):
            token_probability = token_probability[player_race][opp_race]
            logger.debug(f'Setting token probabilty to {player_race} / {opp_race}')

        if (
            player_race in token_information
            and opp_race in token_information[player_race]
        ):
            token_information = token_information[player_race][opp_race]
            logger.debug(f'Setting token information to {player_race} / {opp_race}')

    buildings = list(map(lambda x: x[0], build))
    paths = _generate_next_tokens(
        player_race,
        player_name,
        max_collection_rate,
        buildings,
        token_probability=token_probability,
        token_information=token_information,
    )

    logger.info('Sorting token paths by overall conditional probability')
    paths.sort(key=lambda path: path.probability, reverse=True)

    return paths
