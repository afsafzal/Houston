import os
import json
import csv


def transform_data(data_dir='traces/', command='factory.MAV_CMD_NAV_TAKEOFF'):
    output_filename = "{}.data".format(command)
    header = False
    output_file = open(output_filename, 'w')
    for name in os.listdir(data_dir):
        if not (name.endswith('json')):
            continue
        filename = os.path.join(data_dir, name)
        with open(filename, 'r') as f:
            j = json.load(f)
        for c in j['commands']:
            if c['command']['type'] != command:
                continue
            data = []
            h = []
            for p in sorted(c['command']['parameters']):
                data.append(str(c['command']['parameters'][p]))
                if not header:
                    h.append('p_{}'.format(p))
            for s in sorted(c['states'][0]):
                data.append(str(c['states'][0][s]))
                if not header:
                    h.append('{}0'.format(s))
            for s in sorted(c['states'][-1]):
                data.append(str(c['states'][-1][s]))
                if not header:
                    h.append('{}1'.format(s))
            if not header:
                output_file.write("\t".join(h))
                output_file.write("\n")
                header = True
            output_file.write("\t".join(data))
            output_file.write("\n")
        output_file.flush()
    output_file.close()

def get_min_length(data_dir='traces/', command='factory.MAV_CMD_NAV_TAKEOFF'):
    min_val = 100000000
    temp = []
    for name in os.listdir(data_dir):
        if not (name.endswith('json')):
            continue
        filename = os.path.join(data_dir, name)
        with open(filename, 'r') as f:
            j = json.load(f)
        for c in j['commands']:
            if c['command']['type'] != command:
                continue
            l = len(c['states'])
            temp.append(l)
            if l < min_val:
                min_val = l
    print("AAAA " + str(sorted(temp)))
    return min_val


if __name__=="__main__":
    #l = get_min_length()
    #l = 20
    #print("MIN LENGTH: %d" % l)
    transform_data()
