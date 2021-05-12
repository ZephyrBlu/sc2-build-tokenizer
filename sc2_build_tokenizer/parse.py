import traceback
import logging
from pathlib import PurePath
from collections import defaultdict
from zephyrus_sc2_parser import parse_replay

from sc2_build_tokenizer.dataclasses import ParsedBuild
from sc2_build_tokenizer.constants import IGNORE_OBJECTS

logger = logging.getLogger(__name__)

# 22.4 gameloops per second
SEVEN_MINUTES = 9408
ERRORS = defaultdict(int)


def _recurse(dir_path, fn=None):
    """
    Recursively searches directories to parse replay files
    """
    if dir_path.is_file():
        try:
            replay = parse_replay(dir_path, local=True, network=False)
            logger.info(f'Parsed replay: {dir_path.name}')
            return [fn(replay) if fn else replay]
        except Exception:
            ERRORS[traceback.format_exc()] += 1
            logger.error(f'An error occured during parsing: {traceback.format_exc()}')
            return []

    results = []
    logger.info(f'In directory: {dir_path.name}')
    for obj_path in dir_path.iterdir():
        if obj_path.is_file():
            try:
                replay = parse_replay(obj_path, local=True, network=False)
                logger.info(f'Parsed replay: {obj_path.name}')
            except Exception:
                ERRORS[traceback.format_exc()] += 1
                logger.error(f'An error occured during parsing: {traceback.format_exc()}')
                continue

            results.append(fn(replay) if fn else replay)
        elif obj_path.is_dir():
            logger.info(f'Found new directory: {obj_path.name}')
            results.extend(_recurse(obj_path, fn))

    return results


def extract_builds(replays, end=SEVEN_MINUTES, ignore=IGNORE_OBJECTS):
    """
    9408 = 7min
    """
    logger.info('Parsing builds from replays')
    parsed_replays = replays
    if isinstance(replays, PurePath):
        logger.info('Parsing replay files')
        parsed_replays = _recurse(replays)
        logger.info('Completed parsing replay files')

    logger.info('Extracting builds from replays')

    builds = []
    for replay in parsed_replays:
        replay_builds = []
        for p_id, player in replay.players.items():
            logger.debug(f'Recording {player.race} build')
            player_build = ParsedBuild(player.race, [])

            logger.debug(f'Iterating through player objects')
            for obj in player.objects.values():
                if (
                    not obj.birth_time
                    or obj.birth_time > end
                    or obj.name_at_gameloop(0) in ignore
                ):
                    continue

                if 'BUILDING' in obj.type:
                    player_build.build.append(obj.name_at_gameloop(0))
                    logger.debug(f'Recording {obj.name_at_gameloop(0)}')

            replay_builds.append(player_build)
            logger.debug(f'Finished recording {player.race} build')

        builds.append(replay_builds)
        logger.info('Extracted builds from game')

    logger.info('Completed build extraction')

    return builds
