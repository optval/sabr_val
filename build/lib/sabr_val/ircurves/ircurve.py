import os
import numpy as np
import pandas as pd
from scipy.optimize import newton



class irCurve:
    def __init__(self, yc_curve, left_bounds_extrapolation = True, right_bound_extrapolation = True):
    
        self.yc_curve = yc_curve.copy()
        self.yc_curve['zc_bond'] = 1.0
        self.is_calibrated = False
        self.left_extrapolation = left_bounds_extrapolation
        self.right_extrapolation = right_bound_extrapolation

        self.yc_curve.swap_freq = self.yc_curve.swap_freq.values.astype(int)
        if(np.count_nonzero(self.yc_curve.swap_freq.values<=0)):
            raise Exception(f"Invalid swap freq. Expected to be positive and integer egg. 1, 2, 4")

        self.fit()
        
        
    def fit(self):
        n_knots = self.yc_curve.shape[0]
        for i in range(n_knots):
            freq_i = self.yc_curve.swap_freq.iloc[i]
            tn = self.yc_curve.index[i]
            n_pays = max(self.yc_curve.index[i],1) * freq_i
            rate_i = self.yc_curve.rate.iloc[i] / 100.0
            df_prev = 1.0
            t_prev = 0.0
            if(i):
                df_prev = self.yc_curve.zc_bond.iloc[i-1]  
                t_prev = self.yc_curve.index[i-1]


            dcf_i = 1.0/freq_i if tn >= 1.0 else tn

            df_n = df_prev
            if tn<1.0 :
                df_n = 1.0 / (1.0 + rate_i * dcf_i)
            else :

                try:
                    c = 1.0
                    c_i = rate_i * dcf_i
                    k = 1
                    tk = dcf_i
                    while k < n_pays and tk <= t_prev:
                        c -= c_i*self.zc_bond(tk)
                        k +=1
                        tk += dcf_i

                    def obj_func(x, t1, t2, freq, ci, df, a):

                        #at least 1 coupon is paid between previous swap maturity date and current swap maturity
                        n = max(int ((t2-t1) * freq),1)

                        f = -a
                        for k in range(n):
                            tk = min(t1 + (k+1) / freq,t2)
                            dt = (tk - t1)/(t2 - t1)
                            dfk= pow(x/df, dt)
                            f += (ci + (k==(n-1)))*df*dfk

                        return f
                    
                    df_n = newton(obj_func, df_n, args=(t_prev, tn, freq_i, c_i, df_prev,c), maxiter=200)         
                
                except:
                    raise Exception(f"irCurve failed to boostrap at step {i}, term {tn} , rate {rate_i} ")
                
            self.yc_curve.zc_bond.iloc[i] = df_n
        


        self.is_calibrated = True
        
    
    def zc_bond(self, t: float):
        t0 = self.yc_curve.index[0]
        tn = self.yc_curve.index[-1]

        y = 1.0
        if(t <=t0 and self.left_extrapolation) :
            y =  pow(self.yc_curve.zc_bond.iloc[0], t /t0)
        elif(t >=tn and self.right_extrapolation) :
            y = pow(self.yc_curve.zc_bond.iloc[-1], t /tn)
        elif(t>t0 and t <tn):

            # Find upper neighbours for each interpolation point
            idx = np.searchsorted(self.yc_curve.index.values, t, side='left', sorter=None)

            # Get the two neighbours for each interpolation point
            t0 = self.yc_curve.index[idx - 1]
            t1 = self.yc_curve.index[idx]

            y0 = self.yc_curve.zc_bond.iloc[idx-1]
            y1 = self.yc_curve.zc_bond.iloc[idx]

            # Coefficient for weighting between lower and upper bounds
            dt = (t - t0) / (t1 - t0)

            y = y0 * pow(y1/y0,dt)
        else:
            raise  ValueError(f"Cannot calculate zc_bond.")
        
        
    
        return y
    
    def swapRate(self, t : float, Tn: float, swap_freq : int = 2):
        dt = Tn -t
    
        if(t >=0 and Tn < 1.0) :
            return (self.zc_bond(t)/ self.zc_bond(t+Tn) -1.0) /dt
        elif (t>=0 and Tn >= 1.0):

            df0 = self.zc_bond(t)
            dfn = self.zc_bond(t+Tn)
            
            pv01 = self.PV01( t , Tn, swap_freq)

            rate = (df0 - dfn) / pv01

            return rate
        else :
            raise  ValueError(f"Swap rate cannot have  maturity date lower than start date. ")

    def PV01(self, t : float, Tn: float, swap_freq : int = 2):
        
        n = max(int(Tn * float(swap_freq)),1)
        dcf = 1.0/ float(swap_freq)
            
        pv01 = 0.0
        if(Tn >=dcf ) :

            pv01 = 0
            for i in range(n):
                ti = t + dcf*(i+1)
                pv01 += dcf * self.zc_bond(ti)
        else :
            raise  ValueError(f"Swap rate cannot have  maturity date lower than start date. ")
        
        return pv01
    
    #def zc_bond(self, t, Tn):
    #    return self.zc_bond(Tn) / self.zc_bond(t)
    
