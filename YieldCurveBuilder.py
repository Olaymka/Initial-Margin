from math import * 
import numpy as np
import pandas as pd
import QuantLib as ql

#     --> Get Market quotes of deposits rates up to 1Y / FRA rates / swaps rates (2-3Y up to 15Y)
#     --> Convert quotes to quantlib quotes --> Build depo Helpers and swaps Helpers --> Aggregate both helpers
#     --> Use piecewise function to get yieldcurve handle
#     --> enable extrap

# ------- Yield Curve Builder class --------

class YieldCurveBuilder(object): 
    """
    Build yield curve from market data quotes of different instruments with different maturites
    Return yield curve handle
    """
    
    def __init__(self, settlementDate, dayCounter): 
        self.helpers = []
        self.settlementDate = settlementDate
        self.dayCounter  = dayCounter
    
    def build(self, ):
        """
        lire mes market quotes at ajouter dans le helpers
        """
        pass
    
    
    
    