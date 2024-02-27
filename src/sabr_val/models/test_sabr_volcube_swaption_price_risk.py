import os
import numpy as np
import pandas as pd
from sabr_val.utils import to_year_fraction, to_strike_shift, term_tenor_conversion
from sabr_val.ircurves.ircurve import irCurve
from sabr_val.models.sabr import irSabrVolCube

dir = os.getcwd()

pathe_irvol_file = dir + '\\src\\data\\usd_irvols.csv'
path_ircuve_file = dir + '\\src\\data\\usd_ircurve.csv'

df = pd.read_csv(path_ircuve_file,sep ='\t', index_col =0)

df.index = df.index.map(to_year_fraction)
df.rename(columns={df.columns[0]: "rate"}, inplace = True)
# assumption instruments below 1Y maturity are deposit rates with a single payemnt
df['swap_freq'] = 2
df.loc[df.index<1.0,'swap_freq'] = 1

df_vol = pd.read_csv(pathe_irvol_file,sep ='\t', index_col =0, header =0)
df_vol['Term'], df_vol['Tenor'] = term_tenor_conversion(df_vol.index.to_list())
df_vol.set_index(['Term','Tenor'], inplace=True)

cols = df_vol.columns.to_list()
new_cols = [ to_strike_shift(c) for c in cols]
df_vol.rename(columns = dict(zip(cols, new_cols)), inplace = True)

# construct ir curve
ir_crv = irCurve(df)

# construct ir volcube
ir_volcube = irSabrVolCube(ir_vols = df_vol, ir_curve = ir_crv, shift = 0.00, beta = 0.0)
params1 = ir_volcube._interpolate_calibrated_params( 2.0, 8.0)
print(params1)
params2 = ir_volcube._interpolate_calibrated_params( 5.0, 5.0)
print(params2)


# swaptions price and risk
term = 2.0
tenor = 8.0
texp = term
fwd1 =ir_crv.swapRate(term,tenor)
Ntl1 = 10000000
dK1 = 50 /10000
strike = fwd1+dK1
pay_rec1 = False
pv01 = ir_crv.PV01(term,tenor)*Ntl1
params =  ir_volcube._interpolate_calibrated_params(term, tenor, fwd1)
vol = ir_volcube.get_volatility(texp,term,tenor,fwd1,strike, **{"vol_params": params})
print(f'term {int(term)}Y tenor {int(tenor)}Y')
print(f'forward {fwd1}, pvo1 {pv01}, vol {vol}, model params {params}')
spn1_risk = ir_volcube.swaption_price(texp,term, tenor,fwd=fwd1,strike = strike,pv01=pv01, pay_rec=pay_rec1)
print(f'swaption pv and risk {spn1_risk}')

term = 5.0
tenor = 5.0
texp = term
fwd2 =ir_crv.swapRate(term,tenor)
Ntl2 = 10000000
dK2 = -75 /10000
strike = fwd2+dK2
pay_rec2 = True
pv01 = ir_crv.PV01(term,tenor)*Ntl2
params =  ir_volcube._interpolate_calibrated_params(term, tenor, fwd2)
vol = ir_volcube.get_volatility(texp,term,tenor,fwd2,strike, **{"vol_params": params})
print(f'term {int(term)}Y tenor {int(tenor)}Y')
print(f'forward {fwd2}, pvo1 {pv01}, vol {vol}, model params {params}')
spn2_risk = ir_volcube.swaption_price(texp, term, tenor,fwd=fwd2, strike = strike,pv01=pv01, pay_rec=pay_rec2)
print(f'swaption pv and risk {spn2_risk}')

print('Terminated')