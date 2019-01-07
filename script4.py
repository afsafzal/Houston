import os
import json
import csv


def transform_data(length, data_dir='traces/', command='factory.MAV_CMD_NAV_TAKEOFF'):
    output_filename = "{}.data".format(command)
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
            data = [state['altitude'] for state in c['states']]
            if len(data) < length:
                continue
            n = int(len(data)/length)
            data = [str(data[i*n]) for i in range(length)]
            output_file.write("1.0\t")
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
    l = 20
    print("MIN LENGTH: %d" % l)
    transform_data(l)
