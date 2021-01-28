#------------ Basic Modules Imports ----------------------#
import numpy as np 
import pandas as pd
from math import *
import QuantLib as ql 


# -------- Cap/Floor Object Generation +  Pricing --------#
class makeCapFloor(object):
    """ WHAT? 
    -- interest rate term structure for discounting
    -- interest rate term structure for the floating leg
    -- construction of the capfloor {cap:0, floor:1}
    -- pricing engine to value caps and floors using the Black formula
    
    TODO
    -- Possibility to integrate a volatility surfaces optionlet """
    
    def __init__(self, startDate, maturityDate, iborLegPeriod, strike, iborIndex, iborLegNominal, discountCurveTS,\
                 forecastCurveTS, volatilityTS, capfloorType = 0): 
        self.startDate = startDate
        self.maturityDate = maturityDate
        self.iborLegPeriod = iborLegPeriod
        self.strike = strike
        
        self.discountCurveHandle = ql.RelinkableYieldTermStructureHandle()
        self.forecastCurveHandle = ql.RelinkableYieldTermStructureHandle()
        self.VolTSHandle = volatilityTS
        
        self.discountCurveHandle.linkTo(discountCurveTS)
        self.forecastCurveHandle.linkTo(forecastCurveTS)
        
        self.iborLegNominal = iborLegNominal
        self.iborIndex = iborIndex
        
        self.iborLeg = ql.IborLeg(self.iborLegNominal, self.schedule, self.index)
        self.capfloor = ql.Cap(self.iborLeg, self.strike) if capfloorType == 0 else ql.Floor(self.iborLeg, self.strike)
    
    @property
    def index(self):
        #Create a map between existing ibor index and possible entrance values 
        #Force euribor6M for now
        if self.iborIndex == "euribor 6M": 
            return ql.Euribor6M(self.forecastCurveHandle)
    
    @property
    def schedule(self): 
        return ql.Schedule(self.startDate, self.maturityDate, self.iborLegPeriod, ql.TARGET(), ql.ModifiedFollowing, \
                           ql.ModifiedFollowing, ql.DateGeneration.Backward, False)

    
    def pricer(self, evaluationDate): 
        """
        Compute the CapFloor price from with a valuation date
        """
        ql.Settings.instance().evaluationDate = evaluationDate
        engine = ql.BlackCapFloorEngine(self.discountCurveHandle, self.VolTSHandle)
        self.capfloor.setPricingEngine(engine)
        
        return self.capfloor.NPV()
    
    def sensitivities(): 
        pass
    
