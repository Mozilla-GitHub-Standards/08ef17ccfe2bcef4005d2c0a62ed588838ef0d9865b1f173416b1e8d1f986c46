from copy import deepcopy
import os
import json
from argparse import ArgumentParser

from canary.generator.utils import to_points, to_buckets, plot, read_X_y_from_files
from canary.generator.pipelines_categorical import (
    anomaly_categorical_pipeline,
    not_anomaly_categorical_pipeline,
)
from canary.generator.pipelines_exponential import (
    anomaly_exponential_pipeline,
    not_anomaly_exponential_pipeline,
)
from canary.generator.pipelines_linear import (
    anomaly_linear_pipeline,
    not_anomaly_linear_pipeline,
)


def train_test_split_data(X, y, rate):
    dates = sorted(list(X['data'].keys()))
    train_dates = dates[:int(rate*len(dates))]
    test_dates = dates[int(rate*len(dates)):]
    X_train = deepcopy(X)
    X_train['data'] = {date: X_train['data'][date] for date in train_dates}
    X_test = deepcopy(X)
    X_test['data'] = {date: X_test['data'][date] for date in test_dates}
    y_train = {date: y[date] for date in train_dates}
    y_test = {date: y[date] for date in test_dates}
    return X_train, X_test, y_train, y_test


def change_array_list(X):
    X['data'] = {date: list(X['data'][date]) for date in X['data'].keys()}
    return X


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(dest='files', help='Files with data', nargs='*')
    parser.add_argument(dest='dir',
                        help='Directory, where generated data should be saved')
    parser.add_argument('-p', '--plots', dest='plots', action="store_true",
                        help='Save the plots of generated anomalies', default=False)
    args = parser.parse_args()

    hists, y = read_X_y_from_files(args.files)

    for column in hists.keys():
        new_hist = deepcopy(hists[column])
        new_y = deepcopy(y[column])
        new_hist_train, new_hist_test, new_y_train, new_y_test = \
            train_test_split_data(new_hist, new_y, 0.67)

        new_hist_train = change_array_list(new_hist_train)
        new_hist_test = change_array_list(new_hist_test)

        new_points_test = to_points(new_hist_test)
        new_points_test, new_y_test = anomaly_exponential_pipeline.transform(
            new_points_test, new_y_test
        )
        new_points_test, new_y_test = not_anomaly_exponential_pipeline.transform(
            new_points_test, new_y_test
        )
        new_points_test, new_y_test = anomaly_linear_pipeline.transform(
            new_points_test, new_y_test
        )
        new_points_test, new_y_test = not_anomaly_linear_pipeline.transform(
            new_points_test, new_y_test
        )
        new_hist_test = to_buckets(new_points_test)
        new_hist_test, new_y_test = anomaly_categorical_pipeline.transform(
            new_hist_test, new_y_test
        )
        new_hist_test, new_y_test = not_anomaly_categorical_pipeline.transform(
            new_hist_test, new_y_test
        )
        col_name = column.split('.json')[-2]
        directory_data_X_train = os.path.join(args.dir, col_name + '_X_train.json')
        directory_data_X_test = os.path.join(args.dir, col_name + '_X_test.json')
        directory_data_y_train = os.path.join(args.dir, col_name + '_y_train.json')
        directory_data_y_test = os.path.join(args.dir, col_name + '_y_test.json')
        directory_plot = os.path.join(args.dir, col_name)

        json.dump(new_hist_train, open(directory_data_X_train, 'w'))
        json.dump(new_hist_test, open(directory_data_X_test, 'w'))
        json.dump(new_y_train, open(directory_data_y_train, 'w'))
        json.dump(new_y_test, open(directory_data_y_test, 'w'))

        if args.plots:
            plot(hists[column], y[column], new_hist, new_y, name=directory_plot)

