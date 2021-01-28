from makeSwap import *
from makeSwaption import *
from makeFxOption import *
import numpy as np

class Portfolio(object):
    """portfolio of products"""
    def __init__(self, setOfSwaps, setOfSwaptions=None, setOfCapFloors = None, setOfFxOptions=None):
        self.swaps = setOfSwaps
        self.swaptions = setOfSwaptions
        self.capfloors = setOfCapFloors
        self.fxoptions = setOfFxOptions

    def price_swaps(self, evaluationDate, discountCurve, forecastCurve):
        price = 0.0
        for swap in self.swaps:
            price += swap.pricer(evaluationDate, discountCurve, forecastCurve)
        return price
    
    def get_portfolio_sensitivities(self, evaluationDate, discountCurve): 
        sensitivities = []
        for swap in self.swaps: 
            sensitivities = swap.get_sensitivities(evaluationDate, discountCurve)
#             sensitivities = np.add(sensitivities, swap.sensitivities(evaluationDate, discountCurve))
        return sensitivities
    
#      evaluationDate, discountCurve, forecastCurve --> pricer swap 
#      evaluationDate, discountCurve --> sensitivities



