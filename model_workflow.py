################################
# MODELING WORKFLOW  #
################################

import anomaly_utilities
import modeling_utilities
import rules_detect
import matplotlib.pyplot as plt
import pandas as pd

class ModelWorkflow:
    pass
    """
    """


def ARIMA_detect(df, sensor, params,
                 rules=False, plots=True, summary=True, output=True, site=False):
    """
    """
    print('\nProcessing ARIMA detections.')
    # RULES BASED DETECTION #
    if rules:
        df = rules_detect.range_check(df, params['max_range'], params['min_range'])
        df = rules_detect.persistence(df, params['persist'])
        size = rules_detect.group_size(df)
        df = rules_detect.interpolate(df)
        print(sensor + ' rules based detection complete. Longest detected group = ' + str(size))

    # MODEL CREATION #
    [p, d, q] = params['pdq']
    model_fit, residuals, predictions = modeling_utilities.build_arima_model(df['observed'], p, d, q, summary)
    print(sensor + ' ARIMA model complete.')

    # DETERMINE THRESHOLD AND DETECT ANOMALIES #
    threshold = anomaly_utilities.set_dynamic_threshold(residuals[0], params['window_sz'], params['alpha'], params['threshold_min'])
    threshold.index = residuals.index
    if plots:
        plt.figure()
        anomaly_utilities.plt_threshold(residuals, threshold, sensor)
        plt.show()
    print('Threshold determination complete.')
    detections = anomaly_utilities.detect_anomalies(df['observed'], predictions, residuals, threshold, summary=True)

    # WIDEN AND NUMBER ANOMALOUS EVENTS #
    df['labeled_event'] = anomaly_utilities.anomaly_events(df['labeled_anomaly'], params['widen'])
    df['detected_anomaly'] = detections['anomaly']
    df['all_anomalies'] = df.eval('detected_anomaly or anomaly')
    df['detected_event'] = anomaly_utilities.anomaly_events(df['all_anomalies'], params['widen'])

    # DETERMINE METRICS #
    anomaly_utilities.compare_events(df, params['widen'])
    metrics = anomaly_utilities.metrics(df)
    e_metrics = anomaly_utilities.event_metrics(df)

    # OUTPUT RESULTS #
    if output:
        print('Model type: ARIMA')
        print('Sensor: ' + sensor)
        anomaly_utilities.print_metrics(metrics)
        print('Event based calculations:')
        anomaly_utilities.print_metrics(e_metrics)
        print('Model report complete\n')

    # GENERATE PLOTS #
    if plots:
        plt.figure()
        anomaly_utilities.plt_results(
            raw=df['raw'],
            predictions=detections['prediction'],
            labels=df['labeled_event'],
            detections=df['detected_event'],
            sensor=sensor[0]
        )
        plt.show()

    ARIMA_detect = ModelWorkflow()
    ARIMA_detect.df = df
    ARIMA_detect.model_fit = model_fit
    ARIMA_detect.threshold = threshold
    ARIMA_detect.detections = detections
    ARIMA_detect.metrics = metrics
    ARIMA_detect.e_metrics = e_metrics

    return ARIMA_detect


def LSTM_detect_univar(df, sensor, params, LSTM_params, model_type, name,
                rules=False, plots=True, summary=True, output=True, site=False, model_output=True, model_save=True):
    """
    """
    print('\nProcessing LSTM univariate ' + str(model_type) + ' detections.')
    # RULES BASED DETECTION #
    if rules:
        df = rules_detect.range_check(df, params['max_range'], params['min_range'])
        df = rules_detect.persistence(df, params['persist'])
        size = rules_detect.group_size(df)
        df = rules_detect.interpolate(df)
        print(sensor + ' rules based detection complete. Maximum detected group length = '+str(size))

    # MODEL CREATION #
    if model_type == 'vanilla':
        model = modeling_utilities.LSTM_univar(df, LSTM_params, summary, name, model_output, model_save)
    else:
        model = modeling_utilities.LSTM_univar_bidir(df, LSTM_params, summary, name, model_output, model_save)
    print(sensor + ' ' + str(model_type) + ' LSTM model complete.')
    if plots:
        plt.figure()
        plt.plot(model.history.history['loss'], label='Training Loss')
        plt.plot(model.history.history['val_loss'], label='Validation Loss')
        plt.legend()
        plt.show()

    # DETERMINE THRESHOLD AND DETECT ANOMALIES #
    ts = LSTM_params['time_steps']
    threshold = anomaly_utilities.set_dynamic_threshold(model.test_residuals[0], params['window_sz'], params['alpha'], params['threshold_min'])
    if model_type == 'vanilla':
        threshold.index = df[ts:].index
    else:
        threshold.index = df[ts:-ts].index
    residuals = pd.DataFrame(model.test_residuals)
    residuals.index = threshold.index
    if plots:
        plt.figure()
        anomaly_utilities.plt_threshold(residuals, threshold, sensor)
        plt.show()
    if model_type == 'vanilla':
        observed = df[['observed']][ts:]
    else:
        observed = df[['observed']][ts:-ts]
    print('Threshold determination complete.')
    detections = anomaly_utilities.detect_anomalies(observed, model.predictions, model.test_residuals,
                                                    threshold, summary=True)

    # WIDEN AND NUMBER ANOMALOUS EVENTS #
    if model_type == 'vanilla':
        df_anomalies = df.iloc[ts:]
    else:
        df_anomalies = df.iloc[ts:-ts]
    df_anomalies['labeled_event'] = anomaly_utilities.anomaly_events(df_anomalies['labeled_anomaly'], params['widen'])
    df_anomalies['detected_anomaly'] = detections['anomaly']
    df_anomalies['all_anomalies'] = df_anomalies.eval('detected_anomaly or anomaly')
    df_anomalies['detected_event'] = anomaly_utilities.anomaly_events(df_anomalies['all_anomalies'], params['widen'])

    # DETERMINE METRICS #
    anomaly_utilities.compare_events(df_anomalies, params['widen'])
    metrics = anomaly_utilities.metrics(df_anomalies)
    e_metrics = anomaly_utilities.event_metrics(df_anomalies)

    # OUTPUT RESULTS #
    if output:
        print('Model type: LSTM univariate ' + str(model_type))
        print('Sensor: ' + sensor)
        anomaly_utilities.print_metrics(metrics)
        print('Event based calculations:')
        anomaly_utilities.print_metrics(e_metrics)
        print('Model report complete\n')

    # GENERATE PLOTS #
    if plots:
        plt.figure()
        anomaly_utilities.plt_results(
            raw=df['raw'],
            predictions=detections['prediction'],
            labels=df['labeled_event'],
            detections=df_anomalies['detected_event'],
            sensor=sensor
            )
        plt.show()

    LSTM_detect_univar = ModelWorkflow()
    LSTM_detect_univar.df = df
    LSTM_detect_univar.model = model
    LSTM_detect_univar.threshold = threshold
    LSTM_detect_univar.detections = detections
    LSTM_detect_univar.df_anomalies = df_anomalies
    LSTM_detect_univar.metrics = metrics
    LSTM_detect_univar.e_metrics = e_metrics

    return LSTM_detect_univar


def LSTM_detect_multivar(sensor_array, sensor, params, LSTM_params, model_type, name,
                rules = False, plots=True, summary=True, output=True, site=False, model_output=True, model_save=True):
    """
    """
    print('\nProcessing LSTM multivariate ' + str(model_type) + ' detections.')
    # RULES BASED DETECTION #
    if rules:
        size = dict()
        for snsr in sensor:
            sensor_array[snsr] = rules_detect.range_check(sensor_array[snsr], params[snsr].max_range, params[snsr].min_range)
            sensor_array[snsr] = rules_detect.persistence(sensor_array[snsr], params[snsr].persist)
            size[snsr] = rules_detect.group_size(sensor_array[snsr])
            sensor_array[snsr] = rules_detect.interpolate(sensor_array[snsr])
            print(snsr + ' maximum detected group length = ' + str(size[snsr]))
        print('Rules based detection complete.\n')
    # Create new data frames with raw  and observed (after applying rules) and preliminary anomaly detections for selected sensors
    df_raw = pd.DataFrame(index=sensor_array[sensor[0]].index)
    df_observed = pd.DataFrame(index=sensor_array[sensor[0]].index)
    df_anomaly = pd.DataFrame(index=sensor_array[sensor[0]].index)
    for snsr in sensor:
        df_raw[snsr + '_raw'] = sensor_array[snsr]['raw']
        df_observed[snsr + '_obs'] = sensor_array[snsr]['observed']
        df_anomaly[snsr + '_anom'] = sensor_array[snsr]['anomaly']
    print('Raw data shape: ' + str(df_raw.shape))
    print('Observed data shape: ' + str(df_observed.shape))
    print('Initial anomalies data shape: ' + str(df_anomaly.shape))

    # MODEL CREATION #
    if model_type == 'vanilla':
        model = modeling_utilities.LSTM_multivar(df_observed, df_anomaly, df_raw, LSTM_params, summary, name, model_output, model_save)
    else:
        model = modeling_utilities.LSTM_multivar_bidir(df_observed, df_anomaly, df_raw, LSTM_params, summary, name, model_output, model_save)

    print('multivariate ' + str(model_type) + ' LSTM model complete.\n')
    # Plot Metrics and Evaluate the Model
    if plots:
        plt.figure()
        plt.plot(model.history.history['loss'], label='Training Loss')
        plt.plot(model.history.history['val_loss'], label='Validation Loss')
        plt.legend()
        plt.show()

    # DETERMINE THRESHOLD AND DETECT ANOMALIES #
    ts = LSTM_params['time_steps']
    residuals = pd.DataFrame(model.test_residuals)
    if model_type == 'vanilla':
        residuals.index = df_observed[ts:].index
    else:
        residuals.index = df_observed[ts:-ts].index

    # todo: address this loop
    threshold = []
    for i in range(0, model.test_residuals.shape[1]):
        threshold_df = anomaly_utilities.set_dynamic_threshold(residuals.iloc[:, i], params[sensor[i]].window_sz,
                                                               params[sensor[i]].alpha, params[sensor[i]].threshold_min)
        threshold_df.index = residuals.index
        threshold.append(threshold_df)
        if plots:
            plt.figure()
            anomaly_utilities.plt_threshold(residuals.iloc[:, i], threshold[i], sensor[i])
            plt.show()
    print('Threshold determination complete.')

    if model_type == 'vanilla':
        observed = df_observed[ts:]
    else:
        observed = df_observed[ts:-ts]

    # todo: address this loop
    detections_array = []
    for i in range(0, observed.shape[1]):
        detections_df = anomaly_utilities.detect_anomalies(observed.iloc[:, i], model.predictions.iloc[:, i],
                                                           model.test_residuals.iloc[:, i], threshold[i], summary=True)
        detections_array.append(detections_df)

    # WIDEN AND NUMBER ANOMALOUS EVENTS #
    df_array = []
    # todo: address this loop
    for i in range(0, len(detections_array)):
        all_data = []
        if model_type == 'vanilla':
            all_data = sensor_array[sensor[i]].iloc[ts:]
        else:
            all_data = sensor_array[sensor[i]].iloc[ts:-ts]
        all_data['labeled_event'] = anomaly_utilities.anomaly_events(all_data['labeled_anomaly'], params[sensor[i]].widen)
        all_data['detected_anomaly'] = detections_array[i]['anomaly']
        all_data['all_anomalies'] = all_data.eval('detected_anomaly or anomaly')
        all_data['detected_event'] = anomaly_utilities.anomaly_events(all_data['all_anomalies'], params[sensor[i]].widen)
        df_array.append(all_data)

    # DETERMINE METRICS #
    compare_array = []
    metrics_array = []
    e_metrics_array = []
    # todo: address this loop
    for i in range(0, len(df_array)):
        anomaly_utilities.compare_events(df_array[i], params[sensor[i]].widen)
        metrics = anomaly_utilities.metrics(df_array[i])
        metrics_array.append(metrics)
        e_metrics = anomaly_utilities.event_metrics((df_array[i]))
        e_metrics_array.append(e_metrics)

    # OUTPUT RESULTS #
    if output:
        # todo: address this loop
        for i in range(0, len(metrics_array)):
            print('\nModel type: LSTM multivariate ' + str(model_type))
            print('Sensor: ' + sensor[i])
            anomaly_utilities.print_metrics(metrics_array[i])
            print('Event based calculations:')
            anomaly_utilities.print_metrics(e_metrics_array[i])
        print('Model report complete\n')

    # GENERATE PLOTS #
    if plots:
        # todo: address this loop. need to name them as dictionaries when they are created.
        for i in range(0, len(sensor)):
            plt.figure()
            anomaly_utilities.plt_results(
                raw=df_raw[df_raw.columns[i]],
                predictions=detections_array[i]['prediction'],
                labels=sensor_array[sensor[i]]['labeled_event'],
                detections=df_array[i]['detected_event'],
                sensor=sensor[i]
                )
            plt.show()

    LSTM_detect_multivar = ModelWorkflow()
    LSTM_detect_multivar.sensor_array = sensor_array
    LSTM_detect_multivar.df_observed = df_observed
    LSTM_detect_multivar.df_raw = df_raw
    LSTM_detect_multivar.df_anomaly = df_anomaly
    LSTM_detect_multivar.model = model
    LSTM_detect_multivar.threshold = threshold
    LSTM_detect_multivar.detections_array = detections_array
    LSTM_detect_multivar.df_array = df_array
    LSTM_detect_multivar.compare_array = compare_array
    LSTM_detect_multivar.metrics_array = metrics_array
    LSTM_detect_multivar.e_metrics_array = e_metrics_array

    return LSTM_detect_multivar
