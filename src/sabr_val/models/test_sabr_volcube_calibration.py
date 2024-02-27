import os
import numpy as np
import pandas as pd
from sabr_val.utils import to_year_fraction, to_strike_shift, term_tenor_conversion
from sabr_val.ircurves.ircurve import irCurve
from sabr_val.models.sabr import irSabrVolCube, sabr_normal
import matplotlib.pyplot as plt

dir =  'G:\\Dev\\sabr_val\\' #os.getcwd()

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
ir_volcube = irSabrVolCube(ir_vols = df_vol, ir_curve = ir_crv, shift = 0.0, beta = 0.0)


ir_vols = ir_volcube.ir_vols

fig = plt.figure(figsize=(16, 16))
columns = 4
rows = 4
i = 1
for index, r in ir_vols.iterrows():
    term, tenor = index
    fwd = ir_volcube.ir_curve.swapRate(term, tenor)
    shift, beta = r['shift'], r['beta']
    mkt_vols = r.loc[ir_volcube.d_strikes].values
    mkt_vols = dict(zip(ir_volcube.d_strikes,mkt_vols))
    alpha, rho, nu = ir_vols.loc[index,['alpha','rho','nu']]
    normal = sabr_normal(Fwd = fwd, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
    vols = [normal.vol(K = fwd+shift+dk, T = term) * 10000 for dk in mkt_vols.keys()]
    atm_vol = [mkt_vols[0.0]]
    strikes = [(fwd+dk) * 100 for dk in mkt_vols.keys()]
    
    fig.add_subplot(rows, columns, i)
    plt.plot(strikes, list(mkt_vols.values()), 'x', label = f'mkt vols ')
    plt.plot(strikes, vols, 'k--', label = 'model vols')
    plt.plot([fwd*100], [atm_vol], 'r.', label = 'atm mkt vol')
    plt.grid(True)
    plt.legend()
    #plt.xlabel('strike')
    plt.ylabel(f'bp vol ')
    plt.title(f'{term}Y_{int(tenor)}Y')
    #plt.show()
    #figures = {'im'+str(i): np.random.randint(10, size=(h,w)) for i in range(number_of_im)}
    #plt.clf()
    i+=1

plt.show()
plt.savefig(f'G:\\Dev\\sabr_val\\src\\doc\\charts\\swaption_bp_vols_term={term}Y_maturity={int(tenor)}Y.png')
plt.clf()

i = 1
for index, r in ir_vols.iterrows():
    term, tenor = index
    fwd = ir_volcube.ir_curve.swapRate(term, tenor)
    shift, beta = r['shift'], r['beta']
    mkt_vols = r.loc[ir_volcube.d_strikes].values
    mkt_vols = dict(zip(ir_volcube.d_strikes,mkt_vols))
    alpha, rho, nu = ir_vols.loc[index,['alpha','rho','nu']]
    normal = sabr_normal(Fwd = fwd, shift = shift, beta = beta, alpha = alpha, rho = rho, nu = nu)
    vols = [normal.vol(K = fwd+shift+dk, T = term) * 10000 for dk in mkt_vols.keys()]
    strikes = [(fwd+dk) * 100 for dk in mkt_vols.keys()]
    
    fig.add_subplot(rows, columns, i)
    plt.plot(strikes, np.array(list(mkt_vols.values()))-vols, 'k--', label = f'mkt - model bp vol ')
    plt.plot([fwd*100], [0.0], 'r.', label = 'atm mkt vol')
    plt.grid(True)
    plt.legend()
    #plt.xlabel('strike')
    plt.ylabel(f'error bp vol ')
    plt.title(f'{term}Y_{int(tenor)}Y')
    #plt.show()
    #figures = {'im'+str(i): np.random.randint(10, size=(h,w)) for i in range(number_of_im)}
    #plt.clf()
    i+=1

plt.show()
plt.savefig(f'G:\\Dev\\sabr_val\\src\\doc\\charts\\swaption_calibration_errors_bps.png')
plt.clf()