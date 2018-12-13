# prepare fixed length vector dataset
from os import listdir
from numpy import array
from numpy import savetxt
from pandas import read_csv
 
# return list of traces, and arrays for targets, groups and paths
def load_dataset(data_dir='out/', command='factory.MAV_CMD_NAV_TAKEOFF'):
    # load mapping files
    params = read_csv(data_dir + command + '.csv', header=0)
    params_dict = {p[-1]: list(p[:-1]) for p in params.values}
    print(params_dict)
    # load traces
    sequences = list()
    param_mapping = list()
    for name in listdir(data_dir):
        filename = data_dir + name
        if not name.startswith(command+'_'):
            continue
        df = read_csv(filename, header=0)
        values = df.values
        sequences.append(values)
        param_mapping.append(params_dict[name])
    return sequences, param_mapping
 
# create a fixed 1d vector for each trace with output variable
def create_dataset(sequences, param_mapping):
    # create the transformed dataset
    transformed = list()
    n_vars = 4
    n_steps = 19
    # process each trace in turn
    for i in range(len(sequences)):
        seq = sequences[i]
        vector = list()
        # last - first
        for col in range(len(seq[0])):
            start, end = seq[0][col], seq[-1][col]
            if isinstance(start, float) or isinstance(start, int):
                val = end - start
            elif isinstance(start, bool):
                val = int(end == start)
            elif isinstance(start, str):
                val = int(end == start)
            else:
                print("WTF " + str(type(start)))
                raise Exception
            vector.append(val)

        # last n observations
        # for row in range(1, n_steps+1):
        #     for col in range(n_vars):
        #         vector.append(seq[-row, col])
        # add output
        vector.extend(param_mapping[i])
        # store
        transformed.append(vector)
    # prepare array
    transformed = array(transformed)
    transformed = transformed.astype('float32')
    return transformed
 
# load dataset
sequences, param_mapping = load_dataset()
print("S:{}\nM: {}".format(len(sequences), param_mapping))
# separate traces
#seq1 = [sequences[i] for i in range(len(groups)) if groups[i]==1]
#seq2 = [sequences[i] for i in range(len(groups)) if groups[i]==2]
#seq3 = [sequences[i] for i in range(len(groups)) if groups[i]==3]
# separate target
#targets1 = [targets[i] for i in range(len(groups)) if groups[i]==1]
#targets2 = [targets[i] for i in range(len(groups)) if groups[i]==2]
#targets3 = [targets[i] for i in range(len(groups)) if groups[i]==3]
# create ES1 dataset
#es1 = create_dataset(seq1+seq2, targets1+targets2)
#print('ES1: %s' % str(es1.shape))
#savetxt('es1.csv', es1, delimiter=',')
# create ES2 dataset
es2_train = create_dataset(sequences[:-2], param_mapping)
es2_test = create_dataset(sequences[-2:], param_mapping)
print('ES2 Train: %s' % str(es2_train.shape))
print('ES2 Test: %s' % str(es2_test.shape))
savetxt('es2_train.csv', es2_train, delimiter=',')
savetxt('es2_test.csv', es2_test, delimiter=',')
