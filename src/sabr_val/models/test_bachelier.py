import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import pandas as pd
from sabr_val.models.bachelier import bachelier



t = 365 / 365    #  Time to expiration
K = 105. # fwd price
vol = 0.8/100
Dt = 1.0

shift = 5.* vol * np.sqrt(t)

S = np.linspace(K*(1- shift), K*(1 + shift), 100)    # Let our stock price range between $90 and $110

#  Calculate option prices based on both models
c_bn = bachelier( S, K, t, Dt, vol, c_p = True)
p_bp = bachelier( S, K, t, Dt, vol, c_p = False)

c_bn_risk = c_bn.risk()
p_bn_risk = p_bp.risk()

#  Plot the results

for i in c_bn_risk.keys() :
    risk_type = i
    plt.plot(S, c_bn_risk[risk_type], 'k', label = 'call ' + risk_type)
    plt.plot(S, p_bn_risk[risk_type], 'b.', label = 'put ' + risk_type)
    plt.grid(True)
    plt.legend()
    plt.xlabel('udl price')
    plt.ylabel(f'option risk type {risk_type}')
    plt.close


