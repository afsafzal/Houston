from pandas import read_csv
from sklearn.cluster import KMeans


train_data = read_csv('es2_train.csv', header=None)
test_data = read_csv('es2_test.csv', header=None)
kmeans = KMeans(n_clusters=5, random_state=0).fit(train_data.values)

print("Labels: {}".format(kmeans.labels_))

print("Predict: {}".format(kmeans.predict(test_data.values)))
