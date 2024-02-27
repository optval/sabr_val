import numpy as np
from scipy.stats import norm


class bachelier:
    def __init__(self, f, k, t, Dt, vol, c_p : bool = True, buy_sell : bool = True):
        self.f = f
        self.k = k
        self.t = t
        self.Dt = Dt
        self.vol = vol
        self.cp = 1.0 if c_p else -1.0
        self.long = 1.0 if buy_sell else -1.0


        self.sqrt = np.sqrt(t)
        self.vol_sqrt = vol*self.sqrt
        self.dn = self.cp*(f-k) / self.vol_sqrt

        self.cdf = norm.cdf(self.dn)
        self.pdf = norm.pdf(self.dn)

    
    def pv(self):
        return self.long*self.Dt*self.vol_sqrt * (self.dn * self.cdf + self.pdf)
    
    def delta(self):
        return self.long*self.Dt*self.cp*self.cdf
    
    def vega(self):
        return self.long*self.Dt*self.pdf * self.sqrt
    
    def gamma(self):
        return self.long*self.Dt*self.pdf / self.vol_sqrt
    
    def theta(self):
        return -self.long*self.Dt*self.pdf * 0.5* self.vol / self.sqrt
    
    def vanna(self):
        return -self.long*self.vega()*self.dn / self.vol_sqrt
    
    def volga(self):
        return self.long*self.vega()*self.dn**2 / self.vol
    

    def risk(self) -> dict:

        vals = {}

        vals['pv'] = self.pv()
        vals['delta'] = self.delta()
        vals['vega'] = self.vega()
        vals['gamma'] = self.gamma()
        vals['theta'] = self.theta()
        vals['vanna'] = self.vanna()
        vals['volga'] = self.volga()

        return vals

    

    

