#------------ Basic Modules Imports ----------------------#
import numpy as np 
import pandas as pd
from math import *
import QuantLib as ql 


# -------- Fx Option Object Generation +  Pricing --------#
class makeFxOption(object): 
    """
    
    """
    def __init__(self, domesticRiskFreeTS, foreignRiskFreeTS, volatilityTS, maturityDate, optionType = "Call", exerciceType= "European"): 
        self.domesticRiskFreeTS = ql.RelinkableYieldTermStructureHandle()
        self.foreignRiskFreeTS = ql.RelinkableYieldTermStructureHandle()
        self.volatilityTS = ql.RelinkableBlackVolTermStructureHandle()
        self.optionType = ql.Option.Call if optionType == "Call" else ql.Option.Put
        self.exercise = ql.EuropeanExercise(maturityDate) #if exerciceType == "European" #A compléter avec american exercise
        
        self.domesticRiskFreeTS.linkTo(domesticRiskFreeTS)
        self.foreignRiskFreeTS.linkTo(foreignRiskFreeTS)
        self.volatilityTS.linkTo(volatilityTS)        
    
    def pricer(self, spotValue, evaluationDate, Strike):
        """
        
        """
        self.spot = ql.SimpleQuote(spotValue)
        self.strike = Strike 
        
        #Set up the valuationDate in QuantLib
        ql.Settings.instance().evaluationDate = evaluationDate
        
        #Set the payoff type 
        self.payoff = ql.PlainVanillaPayoff(self.optionType, self.strike)
        #Call the stochastic process
        self.process = ql.GarmanKohlagenProcess(ql.QuoteHandle(self.spot), self.foreignRiskFreeTS, self.domesticRiskFreeTS, self.volatilityTS)
        #Option construction
        europeanOption = ql.VanillaOption(self.payoff, self.exercise)
        #Set the pricing engine
        europeanOption.setPricingEngine(ql.AnalyticEuropeanEngine(self.process))

        return europeanOption.NPV()
    
    def sensitivities(self): 
        passb
    
    def calibrate(self): 
        pass
        
    def deltaGammaVega(self): 
        pass
