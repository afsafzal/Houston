#!/usr/bin/env python3
import json
import yaml
import logging
import argparse
import random

from houston.mission import Mission
from houston.generator.template_based import TemplateBasedMissionGenerator
from houston.generator.resources import ResourceLimits

from settings import sut, initial, environment, build_config


logger = logging.getLogger("houston")  # type: logging.Logger
logger.setLevel(logging.DEBUG)


def setup_logging(verbose: bool = False) -> None:
    log_to_stdout = logging.StreamHandler()
    log_to_stdout.setLevel(logging.DEBUG if verbose else logging.INFO)
    logging.getLogger('houston').addHandler(log_to_stdout)


def parse_args():
    parser = argparse.ArgumentParser(description='Generates missions')
    parser.add_argument('number_of_mission', type=int, action='store',
                       help='number of missions to be generated.')
    parser.add_argument('max_num_commands', type=int, action='store',
                        help='maximum number of commands in a single mission.')
    parser.add_argument('-t', type=str, action='store',
                        help='template of the mission.')
    parser.add_argument('-f', type=str, action='store',
                        help='yaml file of mutants nad their templates.')
    parser.add_argument('--speedup', action='store', type=int,
                        default=1,
                        help='simulation speedup that should be used')
    parser.add_argument('--seed', action='store', type=int,
                        default=1000,
                        help='random seed to be used by random generator.')
    parser.add_argument('--output', action='store', type=str,
                        default='missions.json',
                        help='the file where the results will be stored')
    parser.add_argument('--verbose', action='store_true',
                        default=False,
                        help='verbose logging.')
    return parser.parse_args()


def generate(num_missions: int,
             max_num_commands: int,
             seed: int,
             speedup: int,
             template: str
             ) -> None:
    config = build_config(speedup)
    mission_generator = TemplateBasedMissionGenerator(sut, initial, environment, config, max_num_commands=max_num_commands)
    resource_limits = ResourceLimits(num_missions)
    missions = mission_generator.generate(seed, resource_limits,
                template=template)
    return missions



if __name__ == "__main__":
    args = parse_args()
    setup_logging(args.verbose)
    random.seed(args.seed)
    with open(args.output, "w") as f:
        pass
    if args.t:
        missions = generate(num_missions=args.number_of_mission,
                 max_num_commands=args.max_num_commands,
                 seed=args.seed,
                 speedup=args.speedup,
                 template=args.t)
        mission_descriptions = list(map(Mission.to_dict, missions))
    elif args.f:
        templates = []
        with open(args.f, "r") as f:
            mutants = yaml.load(f, Loader=yaml.FullLoader)
            for m in mutants:
                template = m.get('mission-template')
                if not template:
                    continue
                if isinstance(template, str):
                    templates.append((template, args.number_of_mission, m['uid']))
                elif isinstance(template, list):
                    n_missions = args.number_of_mission
                    for i, t in enumerate(template):
                        if i == len(template)-1:
                            templates.append((t, n_missions, m['uid']))
                        else:
                            r = random.randint(0, n_missions)
                            templates.append((t, r, m['uid']))
                            n_missions -= r
        logger.info("Number of templates: %d", len(templates))
        logger.info("AAAA %s", templates)
        mission_descriptions = []
        for template, num, uid in templates:
            missions = generate(num_missions=num,
                     max_num_commands=args.max_num_commands,
                     seed=args.seed,
                     speedup=args.speedup,
                     template=template)
            for n in missions:
                new_dict = n.to_dict()
                new_dict['mutant'] = uid
                mission_descriptions.append(new_dict)
    else:
        raise Exception("Provide either -t or -f")

    logger.info("Total number of missions: %d", len(mission_descriptions))
    with open(args.output, "w") as f:
        json.dump(mission_descriptions, f, indent=2)
