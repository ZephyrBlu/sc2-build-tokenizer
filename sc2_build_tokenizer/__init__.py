import logging
from logging import NullHandler

from sc2_build_tokenizer.parse import extract_builds
from sc2_build_tokenizer.tokenize import (
    generate_build_tokens,
    generate_token_distributions,
    generate_token_paths,
)
from sc2_build_tokenizer.dataclasses import (
    ParsedBuild,
    TokenizedBuild,
    TokenDistributions,
)

logging.getLogger('zephyrus_sc2_parser').setLevel(logging.ERROR)
logger = logging.getLogger(__name__).addHandler(NullHandler())


def tokenize(replay):
    logger.info('Tokenizing builds with default distributions')

    logger.info('Extracting builds from replays')
    games = extract_builds(replay)

    logger.info('Iterating through replays')

    tokenized = []
    for game in games:
        races = []
        for build in game:
            races.append(build.race)

        logger.info('Generating token paths for builds from current replay')

        builds = []
        for build in game:
            player_race = build.race
            opp_race = races[0] if races[1] == player_race else races[1]
            paths = generate_token_paths(build.build, player_race, opp_race)

            # only take the most likely path
            builds.append(paths[0])

        tokenized.append(builds)
        logger.info('Completed generating tokenized builds from current replay')

    logger.info('Completed generating all tokenized builds from replays')

    return tokenized
