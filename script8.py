import subprocess

import os
import json
import csv


def transform_data(files_filename='files.csv', output_dir='GBDT-out'):
    data_filename = os.path.join(output_dir, 'data.csv')
    meta_filename = os.path.join(output_dir, 'meta')
    files = []
    with open(files_filename, 'r') as f:
        for row in f:
            files.append(row.strip())

    heads = []
    index = 1
    for filename in files:
        result = subprocess.check_output("wc -l {}".format(filename), shell=True).decode().strip()
        linecount = int(result.split(' ')[0])
        heads.append(str(index))
        if index == 1:
            os.system("cp {} {}".format(filename, data_filename))
        else:
            os.system("tail -n {} {} >> {}".format(linecount-1, filename, data_filename))
        index += linecount - 1

    assert len(heads) == len(files)
    with open(meta_filename, 'w') as f:
        f.write(",".join(heads))

if __name__=="__main__":
    transform_data()
