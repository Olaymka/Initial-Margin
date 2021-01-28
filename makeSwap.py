#------------ Basic Modules Imports ----------------------#
import numpy as np 
import pandas as pd
from math import *
import QuantLib as ql 


# -------- Swap Object Generation +  Pricing + sensitivities -------------------#
class makeSwap(object): 
    
    """ Generates vanilla plain swap object
    ===================================
    
    startDate(ql.Date): Start Date
    length(ql.Period): Swap length date
    fixedLegTenor (ql.Period): Fixed leg frequency payment
    nominal(float): Nominal
    fixedRate(float): Rate paid on fixed leg
    index(ql.IborIndex): Index """
    
    def __init__(self, nominal, startDate, length, fixedRate, iborIndex, fixedLegTenor, swapType= ql.VanillaSwap.Payer, spread=0.0, indexMap=None): 
        self.nominal=nominal
        self.startDate=startDate
        self.length=length
        self.fixedRate=fixedRate
        self.fixedLegTenor=fixedLegTenor
        self.swapType=swapType
        self.iborIndex=iborIndex
        self.indexMap = indexMap
        self.spread=spread
        
        #Discount and Forecast curves placeholders
        self.discountCurveHandle = ql.RelinkableYieldTermStructureHandle()
        self.forecastCurveHandle = ql.RelinkableYieldTermStructureHandle()
        
        #SWAP CONVENTION DATES PARAMMS
        self.fixedLegBusinessDayCount = ql.ModifiedFollowing
        self.fixedLegDayCount = ql.Thirty360(ql.Thirty360.BondBasis)
        
    @property
    def maturityDate(self):
        return ql.TARGET().advance(self.startDate, self.length)
    
    @property
    def index(self):
        #Create a map between existing ibor index and possible entrance values 
        #Force euribor6M for now
        if self.iborIndex == "euribor 6M": 
            return ql.Euribor6M(self.forecastCurveHandle)
    
    @property
    def fixedSchedule(self): 
        return ql.Schedule(self.startDate, self.maturityDate, self.fixedLegTenor, self.index.fixingCalendar(),\
                           self.fixedLegBusinessDayCount, self.fixedLegBusinessDayCount, ql.DateGeneration.Backward, False)
    
    @property
    def floatSchedule(self): 
        return ql.Schedule(self.startDate, self.maturityDate, self.index.tenor(), self.index.fixingCalendar(), \
                           self.index.businessDayConvention(), self.index.businessDayConvention(), ql.DateGeneration.Backward, False)
    
    
    # PRICE AND SENSITIVITIES ---------------------------------------------------------------------------------------------------------------------
    def pricer(self, evaluationDate, discountCurve, forecastCurve): 
        """
        Compute swap price at a predetermined valuation date
        """
        #Set up the valuationDate in QuantLib
        ql.Settings.instance().evaluationDate = evaluationDate
        
        #Discount & forecast term structures
        self.discountCurveHandle.linkTo(discountCurve)
        self.forecastCurveHandle.linkTo(forecastCurve)
        
        swap =  ql.VanillaSwap(self.swapType, self.nominal, self.fixedSchedule, self.fixedRate,\
                               self.fixedLegDayCount, self.floatSchedule, self.index, self.spread, self.index.dayCounter())      
        
        datesFixingToAdd = [discountCurve.referenceDate() - ql.Period(i, ql.Days) for i in range(7, 0, -1)]
        for i in range(len(datesFixingToAdd)):
            if self.index.isValidFixingDate(datesFixingToAdd[i]): 
                fixing = self.fixedRate
                self.index.addFixing(datesFixingToAdd[i], fixing)
        
        Engine = ql.DiscountingSwapEngine(self.discountCurveHandle)
        
        swap.setPricingEngine(Engine)

        return swap.NPV(), swap
        
    
    def get_sensitivities(self, evaluationDate, discountCurve): 
        """
        -- Discount curve and forecast curve are the same 
        
        """
        sensitivities = []
        bp = 1e-4
        #Construction of the list of dates
        tenorMonths = [1, 3, 6]
        tenorYears = [1, 2, 3, 5, 10, 15, 20, 30]
        referenceDate = discountCurve.referenceDate() 
        dates = [referenceDate, referenceDate + ql.Period(2, ql.Weeks)]
        dates += [referenceDate + ql.Period(i, ql.Months) for i in tenorMonths]
        dates += [referenceDate + ql.Period(i, ql.Years) for i in tenorYears]
        
        #Spreads initial value list container
        spreads = [ql.QuoteHandle(ql.SimpleQuote(0.0))]*len(dates)
        
        for i in range(1, len(dates)): 
            #set spreads UP and Down list with a specific risk factor shock
            spreads[i]= ql.QuoteHandle(ql.SimpleQuote(0.5*bp))
            discountCurveTiltedUp = ql.SpreadedLinearZeroInterpolatedTermStructure(ql.YieldTermStructureHandle(discountCurve), spreads, dates)

            spreads[i]= ql.QuoteHandle(ql.SimpleQuote(-0.5*bp))
            discountCurveTiltedDown = ql.SpreadedLinearZeroInterpolatedTermStructure(ql.YieldTermStructureHandle(discountCurve), spreads, dates)

            #Get the price 
            shockedUpPrice, x  = self.pricer(evaluationDate, discountCurveTiltedUp, discountCurveTiltedUp)
            shockedDownPrice, x = self.pricer(evaluationDate, discountCurveTiltedDown, discountCurveTiltedDown)
            
            sensitivities.append(shockedUpPrice - shockedDownPrice)
            
            #Relink to base curves
            self.discountCurveHandle.linkTo(discountCurve)
            self.forecastCurveHandle.linkTo(discountCurve)
            
        return sensitivities
            
            


