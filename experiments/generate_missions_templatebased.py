#!/usr/bin/env python3
import json
import logging
import argparse
import random

from houston.mission import Mission
from houston.generator.template_based import TemplateBasedMissionGenerator
from houston.generator.resources import ResourceLimits

from settings import sut, initial, environment, build_config


def setup_logging() -> None:
    log_to_stdout = logging.StreamHandler()
    log_to_stdout.setLevel(logging.DEBUG)
    logging.getLogger('houston').addHandler(log_to_stdout)


def parse_args():
    parser = argparse.ArgumentParser(description='Generates missions')
    parser.add_argument('number_of_mission', type=int, action='store',
                       help='number of missions to be generated.')
    parser.add_argument('max_num_commands', type=int, action='store',
                        help='maximum number of commands in a single mission.')
    parser.add_argument('template', type=str, action='store',
                        help='template of the mission.')
    parser.add_argument('--speedup', action='store', type=int,
                        default=1,
                        help='simulation speedup that should be used')
    parser.add_argument('--seed', action='store', type=int,
                        default=1000,
                        help='random seed to be used by random generator.')
    parser.add_argument('--output', action='store', type=str,
                        default='missions.json',
                        help='the file where the results will be stored')
    return parser.parse_args()


def generate(num_missions: int,
             max_num_commands: int,
             seed: int,
             output_file: str,
             speedup: int,
             template: str
             ) -> None:
    random.seed(seed)
    config = build_config(speedup)
    mission_generator = TemplateBasedMissionGenerator(sut, initial, environment, config, max_num_commands=max_num_commands)
    resource_limits = ResourceLimits(num_missions)
    missions = mission_generator.generate(seed, resource_limits,
                template=template)
    with open(output_file, "w") as f:
        mission_descriptions = list(map(Mission.to_dict, missions))
        json.dump(mission_descriptions, f, indent=2)


if __name__ == "__main__":
    setup_logging()
    args = parse_args()
    generate(num_missions=args.number_of_mission,
             max_num_commands=args.max_num_commands,
             seed=args.seed,
             output_file=args.output,
             speedup=args.speedup,
             template=args.template)
