#------------ Basic Modules Imports ----------------------#
import numpy as np 
import pandas as pd
from math import *
import QuantLib as ql

# -------- Swaption Object Generation +  Pricing --------#
class makeSwaption(object): 
    """
    TODO? 
    -- Integrate swaption for vega computation
    
    """
    def __init__(self, forwardSwap, maturityDate, exerciseType="European", settlementType="PhysicalOTC"):
        self.forwardSwap = forwardSwap
        self.maturityDate = maturityDate
        self.exerciseType = exerciseType
        self.settlementType = settlementType  
        self.exercise = ql.EuropeanExercise(self.maturityDate) # if self.exerciseType=="European"
               
    def pricer(self, evaluationDate, discountCurve, swaptionVols): 
        """
        
        """
        #Set up the valuationDate in QuantLib
        ql.Settings.instance().evaluationDate = evaluationDate
        
        self.termStructure = ql.RelinkableYieldTermStructureHandle()
        self.termStructure.linkTo(discountCurve)
        self.swaptionVols = swaptionVols
        
        swaption = ql.Swaption(self.forwardSwap, self.exercise)
        
        engine = ql.BlackSwaptionEngine(self.termStructure, self.swaptionVols)
        
        swaption.setPricingEngine(engine)
        
        return swaption.NPV()
    
    def sensitivities(self): 
        pass
        