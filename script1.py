import os
import json
import csv


def transform_data(data_dir='record/', output_dir='out/'):
    for name in os.listdir(data_dir):
        if not (name.startswith('mission') and name.endswith('jsn')):
            continue
        m_num = int(name[len('mission#'):-len('.jsn')])
        filename = os.path.join(data_dir, name)
        with open(filename, 'r') as f:
            for l in f:
                c = json.loads(l)
                new_filename_temp = "{}_{}_{}.csv".format(c['command']['type'], m_num, c['index'])
                new_filename = os.path.join(output_dir, new_filename_temp)
                keys = list(c['states'][0].keys())
                with open(new_filename, 'w') as output_file:
                    dict_writer = csv.DictWriter(output_file, keys)
                    dict_writer.writeheader()
                    dict_writer.writerows(c['states'])
                param_filename = os.path.join(output_dir, c['command']['type'] + ".csv")
                param_keys = list(c['command']['parameters'].keys())
                param_keys.append('filename')
                print_header = False
                if not os.path.exists(param_filename):
                    print_header = True
                with open(param_filename, 'a') as output_file:
                    dict_writer = csv.DictWriter(output_file, param_keys)
                    if print_header:
                        dict_writer.writeheader()
                    p = c['command']['parameters']
                    p['filename'] = new_filename_temp
                    dict_writer.writerow(p)

if __name__=="__main__":
    transform_data()
