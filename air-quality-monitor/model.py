import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

def model_1(D, alpha, beta, C_out, C_in, t, C_t, window_open, x=1):
    if window_open:
        return (C_out-C_in)*np.sqrt((2*x**2)/(np.pi*D*t**3))*np.exp((-x**2)/(4*D*t)) - alpha*(C_t - beta)
    else:
        return - alpha*(C_t - beta)


def time_series(D, alpha, beta, C_t, C_out, C_in, t, window_open, C_0, dt, x=1):
    return  C_t - (C_0 + dt*model_1(C_out, C_in, D, t, C_t, alpha, beta, window_open, x))

if __name__ == "__main__":
    df = pd.read_csv('air_data.csv')
    air_quality = df['AQI'][:-1]
    outside_air_quality = df['Outside AQI'][:-1]
    C_t = df['AQI'][1:]
    C_0 = df['AQI'][:-1]
    window_open = df['Window open'][:-1]



    res = minimize(time_series, x0=(0.1, 0.1, 0.1), args=(C_t, outside_air_quality, air_quality, np.arange(len(C_0)), window_open, C_0, 300), method='Nelder-Mead', tol=1e-6)
    print(res.x)

