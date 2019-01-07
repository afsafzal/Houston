import os
import json
import csv
import yaml

def create_trace_file(data_dir='traces/', output_filename='ardu.dtrace'):
    ppt_val = """
{name}:::{sub}
this_invocation_nonce
{nonce}
"""
    var_val = """{name}
{val}
1
"""
    with open(output_filename, 'w') as f:
        pass

    for fname in os.listdir(data_dir):
        if not (fname.endswith('json')):
            continue
        filename = os.path.join(data_dir, fname)
        with open(filename, 'r') as f:
            j = json.load(f)
        index = 0
        for c in j['commands']:
            nonce='{}-{}'.format(fname, index)
            parameters = ''
            for name in c['command']['parameters'].keys():
                parameters += var_val.format(name='p_{}'.format(name), val=c['command']['parameters'][name])
            state_b = c['states'][0]
            state_e = c['states'][-1]
            states = ''
            for name in state_b.keys():
                states += var_val.format(name=name, val=state_b[name])
            with open(output_filename, 'a') as f:
                f.write(ppt_val.format(name=c['command']['type'], sub='ENTER', nonce=nonce))
                f.write(parameters)
                f.write(states)
            states = ''
            for name in state_e.keys():
                states += var_val.format(name=name, val=state_e[name])
            with open(output_filename, 'a') as f:
                f.write(ppt_val.format(name=c['command']['type'], sub='EXIT', nonce=nonce))
                f.write(parameters)
                f.write(states)
            
            index += 1




def create_decl_file(command_yml_filename='commands.yml', output_filename='ardu.decl'):
    topping = """decl-version 2.0
input-language houston
var-comparability implicit
"""
    var_decl = """variable {name}
  var-kind variable
  dec-type {type}
  rep-type {type}
  flags {flags}
  comparability 22
"""
    ppt_decl = """
ppt {name}:::{sub}
ppt-type {type}
"""
    state_vars = [
        {'name': 'home_latitude',
            'type': 'float',
            'flags': ''
            },
        {'name': 'home_longitude',
            'type': 'float',
            'flags': ''
            },
        {'name': 'altitude',
            'type': 'float',
            'flags': ''
            },
        {'name': 'latitude',
            'type': 'float',
            'flags': ''
            },
        {'name': 'longitude',
            'type': 'float',
            'flags': ''
            },
        {'name': 'armable',
            'type': 'boolean',
            'flags': ''
            },
        {'name': 'armed',
            'type': 'boolean',
            'flags': ''
            },
        {'name': 'mode',
            'type': 'java.lang.String',
            'flags': 'is_enum'
            },
        {'name': 'vx',
            'type': 'float',
            'flags': ''
            },
        {'name': 'vy',
            'type': 'float',
            'flags': ''
            },
        {'name': 'vz',
            'type': 'float',
            'flags': ''
            },
        {'name': 'pitch',
            'type': 'float',
            'flags': ''
            },
        {'name': 'yaw',
            'type': 'float',
            'flags': ''
            },
        {'name': 'roll',
            'type': 'float',
            'flags': ''
            },
        {'name': 'heading',
            'type': 'float',
            'flags': ''
            },
        {'name': 'airspeed',
            'type': 'float',
            'flags': ''
            },
        {'name': 'groundspeed',
            'type': 'float',
            'flags': ''
            },
        {'name': 'ekf_ok',
            'type': 'boolean',
            'flags': ''
            },
        {'name': 'throttle_channel',
            'type': 'float',
            'flags': ''
            },
        {'name': 'roll_channel',
            'type': 'float',
            'flags': ''
            }
        ]

    states = ''
    for s in state_vars:
        states += var_decl.format(**s)
    with open(command_yml_filename, 'r') as f:
        all_commands = yaml.load(f)['commands']

    with open(output_filename, 'w') as f:
        f.write(topping)

    for c in all_commands:
        parameters = ''
        for i in range(1, 8):
            p = 'p{}'.format(i)
            if p in c:
                param = None
                p_name = 'p_{}'.format(c[p]['name'])
                typ = c[p]['value']['type']
                if typ == 'discrete':
                    p_dic = {'name': p_name,
                            'type': 'int',
                            'flags': 'is_enum nomod'
                        }
                elif typ == 'continuous':
                    p_dic = {'name': p_name,
                            'type': 'float',
                            'flags': 'nomod'
                            }
                parameters += var_decl.format(**p_dic)
        with open(output_filename, 'a') as f:
            f.write(ppt_decl.format(name='factory.{}'.format(c['name']), sub='ENTER', type='enter'))
            f.write(parameters)
            f.write(states)
            f.write('\n')
            f.write(ppt_decl.format(name='factory.{}'.format(c['name']), sub='EXIT', type='exit'))
            f.write(parameters)
            f.write(states)


if __name__=="__main__":
#    create_decl_file()
    create_trace_file()
