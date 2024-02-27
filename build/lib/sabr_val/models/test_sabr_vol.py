import os
import numpy as np
import pandas as pd
from sabr_val.models.sabr import sabr_normal




f = 2014
beta = 1.0
alpha = 3.24
rho = -0.998
nu = 1.69
sabr_vol_test = sabr_normal(Fwd = f, shift = 0.0, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test.vol(K = f, T = 0.48)
print(vol)
vol2 = 0.0


T = 10.0
f = 0.02
K = 0.02
shift = 0.0
beta = 0.0
alpha = 0.5/100
rho = 0.5
nu = 20/100
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = 0.01
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = 0.0
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = -0.01
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = -0.02
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = 0.03
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = 0.05
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = 0.07
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
K = 0.09
sabr_vol_test2 = sabr_normal(Fwd = f, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
vol = sabr_vol_test2.vol(K = K, T = T)
print(vol)
vol2 = 0.0
    
