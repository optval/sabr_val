import os
import numpy as np
import pandas as pd
from sabr_val.utils import to_year_fraction
from sabr_val.ircurves.ircurve import irCurve

dir = os.getcwd()


path_ircuve_file = dir + '\\src\\data\\usd_ircurve.csv'

df = pd.read_csv(path_ircuve_file,sep ='\t', index_col =0)
df.rename(columns={df.columns[0]: "rate"}, inplace = True)
df.index = df.index.map(to_year_fraction)
# assumption instruments below 1Y maturity are deposit rates with a single payemnt
df['swap_freq'] = 2
#df.loc[df.index<1.0,'swap_freq'] = 1


ir_crv = irCurve(df)

print(ir_crv.zc_bond(1.0))
print(ir_crv.swapRate(0.5,1.0))
print(ir_crv.PV01(0.5,1.0))
print(ir_crv.zc_bond(2.0))
print(ir_crv.swapRate(0.0,2.0))
print(ir_crv.PV01(0.0,2.0))
print(ir_crv.swapRate(2.0,2.0))
print(ir_crv.PV01(2.0,2.0))
print(ir_crv.zc_bond(3.0))
print(ir_crv.swapRate(0.0,3.0))
print(ir_crv.zc_bond(4.0))
print(ir_crv.swapRate(0.0,4.0))


# ir_volcube.price(Texp, T, Tn, K, c_p)
# ir_volcube.delta(Texp, T, Tn, K, c_p)
# ir_volcube.vega(Texp, T, Tn, K, c_p)
# ir_volcube.gamma(Texp, T, Tn, K, c_p)
# ir_volcube.theta(Texp, T, Tn, K, c_p)
# ir_volcube.carry(Texp, T, Tn, K, c_p)