import os
import re
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.optimize import newton
from sabr_val.ircurves.ircurve import irCurve
from sabr_val.models.bachelier import bachelier



class sabr_normal:
    def __init__(self, Fwd, shift = 0.0, beta = 0.5, alpha = 0.1, rho = 0.5, nu = 0.1):
        self.Fwd = Fwd
        self.shift = shift
        self.beta = beta
        self.alpha = alpha
        self.rho = rho
        self.nu = nu

        self.eps = 1e-06

        if  (self.alpha <= 0.0):
            raise  ValueError(f"alpha should be positive. ")
    
        if  (self.beta < 0.0):
            raise  ValueError(f"beta should be positive. ")
        
        if abs(1.0 - self.beta)<self.eps and  (self.Fwd + self.shift) < self.eps :
            raise  ValueError(f"when beta is close to 1 lognormal, Shifted forward rate should be positive. ")
        
        if (self.nu < 0.0):
            raise  ValueError(f"nu should be non negative. ")
    
    def vol(self, K : float, T : float):
        atm = self._f_minus_k_ratio(K)
        A = self._g_k(K)
        B = 0.0
        if abs(self.beta) > self.eps:
            B = 0.25 * self.rho * self.nu * self.alpha * self.beta * pow((self.Fwd + self.shift)*(K + self.shift), 0.5*(self.beta - 1))
        C = (2-3*self.rho**2) * self.nu**2 / 24.0
        return atm * (1.0 + (A + B + C) * T)
    

    def _zeta(self, K):
        
        m_beta = 1.0 - self.beta

        if abs(self.beta) < self.eps:
            zeta = 1 / self.alpha * (self.Fwd - K)
        elif abs(m_beta) < self.eps:
            zeta = 1 / self.alpha * np.log((self.Fwd + self.shift)/(K + self.shift))
        else:
            zeta = 1 / (self.alpha * m_beta) *(pow(self.Fwd + self.shift,m_beta)-pow(K + self.shift,m_beta))

        if (self.nu > 0.0):
            zeta *= self.nu

        return zeta
        

    
    def _x(self, K):

        zeta = self._zeta(K)

        if (self.nu > 0.0):
            a = (1 - 2*self.rho*zeta + zeta**2)**.5 - self.rho + zeta
            b = 1 - self.rho
            return np.log(a / b) / self.nu
        else:
            return zeta
        
    def _f_minus_k_ratio(self, K):

        if abs(self.Fwd-K) > self.eps:
            return (self.Fwd - K) / self._x(K)
        else:
            if abs(self.Fwd + self.shift)>self.eps:
                return self.alpha * pow(self.Fwd + self.shift, self.beta)
            else:
                return self.alpha * pow(self.eps, self.beta)
        
    def _g_k(self, K):

        g_k = 0.0
        m_beta = 1.0 - self.beta
        if(abs(m_beta)<self.eps):
            g_k = -self.alpha**2/24.0
        elif(abs(self.beta)<self.eps):
            g_k = 0.0
        else:
            g_k = self.alpha**2/24.0 * self.beta * (self.beta - 2) * pow((self.Fwd + self.shift)*(K + self.shift), self.beta - 1)
        
        return g_k


class irSabrVolCube:
    def __init__(self, ir_vols, ir_curve: irCurve, shift = 0.0, beta = 0.5, alpha = 2/100, rho = 0.5, nu = 0.3, left_bounds_extrapolation = True, right_bound_extrapolation = False):
    
        self.ir_vols = ir_vols
        self.ir_curve = ir_curve
        self.left_extrapolation = left_bounds_extrapolation
        self.right_extrapolation = right_bound_extrapolation

        self.d_strikes = self.ir_vols.columns.to_list()

        self.ir_vols['shift'] = shift
        self.ir_vols['beta'] = beta
        self.ir_vols['alpha'] = alpha
        self.ir_vols['rho'] = rho
        self.ir_vols['nu'] = nu

        if (self.ir_vols.shape[0]==0):
            raise  ValueError(f"Missing calibration data. ")

        self.is_calibrated = False

        self.fit()
        
    
    def alpha(self,fwd, shift, v_atm_n, texp, beta, rho, nu):
        """
        Compute SABR parameter alpha from an ATM normal volatility.
        Alpha is determined as the root of a 3rd degree polynomial. It returns the closest positive real root
        """
        f = (fwd+shift)
        f_ = f ** (1 - beta)
        p = [
            beta * (beta - 2) / (24 * f_**2) * texp * f**beta,
            f**beta * rho * beta * nu * texp / (4 * f_),
            (1 + nu**2 * (2 - 3*rho**2)*texp / 24) * f**beta,
            -v_atm_n/10000
        ]
        roots = np.roots(p)
        roots_real = np.extract(np.isreal(roots), np.real(roots))
        alpha_first_guess = v_atm_n/10000 * f**(-beta)
        i_min = np.argmin(np.abs(roots_real - alpha_first_guess))
        return roots_real[i_min]
            
    def fit(self, initial_guess = [0.5, 0.20]): # initial_guess = [0.01, 0.5, 0.20]

        for index, r in self.ir_vols.iterrows():
            
            term, tenor = index

            try:
                fwd = self.ir_curve.swapRate(term, tenor)
                shift, beta = r['shift'], r['beta']
                mkt_vols = r.loc[self.d_strikes].values
                mkt_vols = dict(zip(self.d_strikes,mkt_vols))
                weights = np.ones(len(mkt_vols)) 

                def vol_square_error(x, mkt_vols,weights, term,fwd, shift, beta):
                    alpha0 = self.alpha(fwd, shift, mkt_vols[0.0], term, beta, x[0], x[1])
                    normal = sabr_normal(Fwd = fwd, shift = shift, beta = beta, alpha = alpha0, rho = x[0], nu = x[1])
                    vols = [normal.vol(K = fwd+shift+dk, T = term) * 10000 for dk in mkt_vols.keys()]
                    return weights @ ((vols - np.array(list(mkt_vols.values())))**2) / len(mkt_vols)

                x0 = np.array(initial_guess)
                bounds = [(-0.9999, 0.9999), (0.00001, None)]
                res = minimize(vol_square_error, x0, args=(mkt_vols,weights, term,fwd,shift,beta), method='L-BFGS-B', bounds=bounds)
                alpha = self.alpha(fwd, shift, mkt_vols[0.0], term, beta, res.x[0], res.x[1])
                self.ir_vols.loc[index,['alpha','rho','nu']] = [alpha] + list(res.x)
                mse = np.sqrt(vol_square_error(res.x, mkt_vols,weights, term,fwd, shift, beta))
                normal = sabr_normal(Fwd = fwd, shift = shift, beta = beta, alpha = alpha, rho = res.x[0], nu = res.x[1])
                vols = [normal.vol(K = fwd+shift+dk, T = term) * 10000 for dk in mkt_vols.keys()]
                print(f"Calibration was succesful for term {term}, tenor {tenor} average bp difference {mse}")
                print(f'model vols vs market vols {vols} {list(mkt_vols.values())}')
            except :
                raise  ValueError(f"Calibration failed. term {term}, tenor {tenor}")

        self.is_calibrated = True   


    def _interpolate_calibrated_params(self, term, tenor, fwd=None, d_atm_vol=0.0)-> dict:

        if(self.is_calibrated):
            ir_params = self.ir_vols.reset_index(). loc[:, ["Term", "Tenor", 0.0,'shift','beta','alpha','rho','nu']]
            terms = np.sort(ir_params.Term.unique())
            tenors = np.sort(ir_params.Tenor.unique())

            ir_params.set_index(['Term', 'Tenor'], inplace = True)

            if(self.right_extrapolation==False ) :
                if (tenor>tenors[-1]) :
                    raise Exception(f"Tenor is longer than last available tenor . Requested tenor {tenor} and last available is {tenors[-1]}")
                
                if (term>terms[-1]) :
                    raise Exception(f"Expiry is longer than last available expiry . Requested expiry {term} and last available is {terms[-1]}")
            
            if(self.left_extrapolation==False ) :
                if (tenor<tenors[0]) :
                    raise Exception(f"Tenor is shorter than shortest available tenor . Requested tenor {tenor} and shorted available is {tenors[0]}")
                
                if (term<terms[0]) :
                    raise Exception(f"Expiry is shorter than shortest available expiry . Requested expiry {term} and shorted available is {terms[0]}")
                
            atm_vol = -1.0
            y = []

            if(term<=terms[0] and tenor<=tenors[0]) :
                y = ir_params.loc[(terms[0],tenors[0])]
                # calculate implied term atm vol
                atm_vol = y[0.0]
            elif (term>=terms[-1] and tenor>=tenors[-1]) :
                y = ir_params.loc[(terms[-1],tenors[-1])]
                # calculate implied term atm vol
                atm_vol = y[0.0]
            elif (term<=terms[0] and tenor>=tenors[-1]) :
                y = ir_params.loc[(terms[0],tenors[-1])]
                # calculate implied term atm vol
                atm_vol = y[0.0]
            elif (term>=terms[-1] and tenor<=tenors[0]) :
                y = ir_params.loc[(terms[-1],tenors[0])]
                # calculate implied term atm vol
                atm_vol = y[0.0]
            elif (term<=terms[0] and tenor<tenors[-1]) :
                # Find upper neighbours for each interpolation point
                idx1 = np.searchsorted(tenors, tenor, side='left', sorter=None) 
                dx1 = (tenor - tenors[idx1-1])/(tenors[idx1]-tenors[idx1-1]) 

                y = ir_params.loc[(terms[0],tenors[idx1-1])] * (1 - dx1)+ ir_params.loc[(terms[0],tenors[idx1])]*dx1
                # calculate implied term atm vol
                atm_vol = y[0.0]

            elif (term<terms[-1] and tenor<=tenors[0]) :
                # Find upper neighbours for each interpolation point

                idx2 = np.searchsorted(terms, term, side='left', sorter=None)  
                dx2 = (term - terms[idx2-1])/(terms[idx2]-terms[idx2-1])

                y1 = ir_params.loc[(terms[idx2-1],tenors[0])] 
                y2 = ir_params.loc[(terms[idx2],tenors[0])]

                # calculate implied term atm vol by interpolating atm mkt term variance
                atm_vol = np.sqrt((y1[0.0]**2*terms[idx2-1]*(1-dx2)+ y2[0.0]**2*terms[idx2]*dx2) / term)

                y = y1*(1-dx2) + y2*dx2
                y[0.0] = atm_vol

            else:

                # Find upper neighbours for each interpolation point
                idx1 = np.searchsorted(tenors, tenor, side='left', sorter=None) 
                idx2 = np.searchsorted(terms, term, side='left', sorter=None)  

                dx1 = (tenor - tenors[idx1-1])/(tenors[idx1]-tenors[idx1-1])   
                dx2 = (term - terms[idx2-1])/(terms[idx2]-terms[idx2-1])

                y1 = ir_params.loc[(terms[idx2-1],tenors[idx1-1])] * (1 - dx1)+ ir_params.loc[(terms[idx2-1],tenors[idx1])]*dx1
                y2 = ir_params.loc[(terms[idx2],tenors[idx1-1])] * (1 - dx1)+ ir_params.loc[(terms[idx2],tenors[idx1])]*dx1
                # calculate implied term atm vol by interpolating atm mkt term variance
                atm_vol = np.sqrt((y1[0.0]**2*terms[idx2-1]*(1-dx2)+ y2[0.0]**2*terms[idx2]*dx2) / term)

                y = y1*(1-dx2) + y2*dx2
                y[0.0] = atm_vol

            fwdRate = self.ir_curve.swapRate(term, tenor) if fwd is None else fwd
            shift, beta, rho, nu = y['shift'], y['beta'], y['rho'], y['nu']
            mkt_vol = atm_vol+d_atm_vol

            y['alpha'] = self.alpha(fwdRate,  y['shift'], mkt_vol, term,  y['beta'], y['rho'], y['nu'])    

            return dict(y)
               
        else:
            raise  ValueError(f"Model is not being calibrated yet. term {term}, tenor {tenor}")
    

    def get_volatility(self, texp, term, tenor, fwd, strike, **kwargs):

        params =  {} # self._interpolate_calibrated_params(term, tenor)
        if kwargs.__len__() != 0 and 'vol_params' in kwargs:
            params = kwargs.get('vol_params')
        else:
            params =  self._interpolate_calibrated_params(term, tenor, fwd)

        normal = sabr_normal(Fwd = fwd, shift = params['shift'], beta = params['beta'], alpha = params['alpha'], rho = params['rho'], nu = params['nu'])
        vol = normal.vol(K = strike+params['shift'], T = texp)

        return vol
    
    def swaption_price(self, texp, term, tenor, fwd, strike, pv01, pay_rec :bool = True, buy_sell : bool = True) -> dict :
    
        params =  self._interpolate_calibrated_params(term, tenor, fwd)
        vol = self.get_volatility(texp,term,tenor,fwd,strike, **{"vol_params": params})
        
        bn_model = bachelier(fwd,strike, t= term, Dt = pv01, vol = vol, c_p = True if pay_rec else False,buy_sell=buy_sell)

        vals = {}
        risk = bn_model.risk()
        #risk dynamics adjustments
        pv = risk['pv']
        delta = risk['delta']
        vega = risk['vega']
        gamma = risk['gamma']
        vanna = risk['vanna']
        volga = risk['volga']   
        theta = risk['theta']

        dfwd = 0.0001
        d_atm_vol = 0.0001

        shift = params['shift']
        beta = params['beta']
        alpha = params['alpha']
        rho = params['rho']
        nu = params['nu']

        
        params =  self._interpolate_calibrated_params(term, tenor, fwd,d_atm_vol=d_atm_vol)
        vol1 = self.get_volatility(texp,term,tenor,fwd,strike, **{"vol_params": params})
        dvol_dfwd = 0.0
        dvol_dalpha=(vol1-vol)/(params['alpha'] - alpha)
        scale = pow(fwd + shift, -beta) if beta > 0.0 else 1.0
        vega_adj =  (dvol_dfwd + dvol_dalpha*rho * nu * scale)
        delta_adj = vega * vega_adj
        delta += delta_adj

        vals['pv'] = pv
        vals['delta'] = delta
        vals['delta_adj'] = delta_adj
        vals['gamma'] = gamma
        vals['vega'] = vega *(dvol_dalpha + dvol_dfwd*rho*scale / nu)
        vals['vega_adj'] = vega *(dvol_dalpha + dvol_dfwd*rho*scale / nu - 1.0)

        # carry adj and theta is assumend to be 1 calendar day. it should be 1 business day
        dt = 1.0/365
        params =  self._interpolate_calibrated_params(term-dt, tenor, fwd)
        vol1 = self.get_volatility(texp-dt,term,tenor,fwd,strike, **{"vol_params": params})
        dvol_dt = (vol1 - vol) /dt
        carry_adj = (1.0/self.ir_curve.zc_bond(dt) -1.0)/dt
        vals['theta'] = theta + carry_adj*pv + vega*dvol_dt
        vals['vanna'] = vanna
        vals['volga'] = volga

        return vals





