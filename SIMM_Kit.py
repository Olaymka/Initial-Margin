from math import * 
import numpy as np
import pandas as pd
import QuantLib as ql
from makeSwap import *
from Portfolio import *

#Interest rate risk weights for regular currencies (e.g.: USD, EUR, GBP)
IR_risksWeights = {'2W': 116, '1M':106, '3M':94, '6M':71, '1Y':59, '2Y':52, '3Y':49, '5Y':51, '10Y':51, '15Y':51, '20Y':54, '30Y':62}
tenors = ['2W', '1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '10Y', '15Y', '20Y', '30Y']

#ISDA schedule for GRID method
im_Schedule = pd.DataFrame(np.array([["[0,2]",0.02,0.15,0.06,0.01,0.15],["[2,5]",0.05,0.15,0.06,0.02,0.15],[">5",0.1,0.15,0.06,0.04,0.15]]),
              columns = ["Maturity (in years)", "Credit","Equity","FX","Rates", "Other"])
im_Schedule = im_Schedule.astype({"Credit": float, "Equity": float, "FX": float, "Rates": float, "Other": float})

#Create Portfolio of instruments ---------------------------------------------------------------------------------
def create_portfolio_swaps(nominalsVect,StartDateVect,maturitiesVect,fixedRateVect,indexVect,fixedLegtenors,swapTypes): 
    portfolio_Size = len(nominalsVect) 
    #If instrument type == swaps
    setofSwaps = [makeSwap(nominalsVect[i],StartDateVect[i],maturitiesVect[i],fixedRateVect[i],indexVect[i],fixedLegtenors[i],swapTypes[i])\
                  for i in range(portfolio_Size)]
    return Portfolio(setofSwaps)
    
#Grid-schedule method --------------------------------------------------------------------------------------------
def IM_Grid_method(im_Schedule,  pricingParameters, evaluationDate, discountCurve, forecastCurve):
    """
    TODO? 
    -- Works only for rates products. Still to be adapted for the remaining products classes
    """
    init_m = 0
    portfolio_Size = len(pricingParameters[0])
    portfolio = create_portfolio_swaps( *pricingParameters )
    portfolio_npv = np.array( [portfolio.swaps[d].pricer(evaluationDate, discountCurve, forecastCurve)[0] for d in range(portfolio_Size)])
    for i in range(portfolio_Size):
        if pricingParameters[2][i] <= ql.Period("5Y") and pricingParameters[2][i] > ql.Period("2Y"):
            margin_ratio = im_Schedule.loc[1,"Rates"]
            init_m += margin_ratio * pricingParameters[0][i]
        
        elif pricingParameters[2][i] <= ql.Period("0Y") and pricingParameters[2][i] > ql.Period("2Y"):
            margin_ratio = im_Schedule.loc[0,"Rates"]
            init_m += margin_ratio * pricingParameters[0][i]
        else:
            margin_ratio = im_Schedule.loc[2,"Rates"]
            init_m += margin_ratio * pricingParameters[0][i]

    NGR = np.absolute(np.sum(portfolio_npv))/np.sum(np.absolute(portfolio_npv)) if np.sum(portfolio_npv)/np.sum(np.absolute(portfolio_npv))>0 else 0
    return [np.sum(portfolio_npv), 0.4*init_m + 0.6*init_m*NGR, init_m, NGR] 

#SIMM method implementation ---------------------------------------------------------------------------------------
def concentrationRiskFactor(sensitivities, concentrationThreshold):
    """
    Compute the interest rate concentration risk factor for weighted sensitivities calculation 
    """
    return max(1, sqrt(abs(sum(sensitivities))/concentrationThreshold))

def weightedSensitivies(sensitivities, concentrationThreshold): 
    """
    weighted sensitivities calculation
    """
    return concentrationRiskFactor(sensitivities, concentrationThreshold)* np.multiply(sensitivities, [IR_risksWeights[tenors[k]] for k in range(len(IR_risksWeights))])

def deltaMargin_IR(sensitivities, concentrationThreshold, tenor_correl=None):
    """
    Get delta Margin within a specific currency across indices yield term structures
    Residual part with correlation within tenors to be added
    """
    weighted_sensitivities = weightedSensitivies(sensitivities, concentrationThreshold)
    return sqrt(sum(weighted_sensitivities**2))

def Compute_IM(evaluationDate, pricingParameters, discountCurve, concentrationThreshold): 
    """
    
    """
    portfolio = create_portfolio_swaps(*pricingParameters)
    sensitivities = portfolio.get_portfolio_sensitivities(evaluationDate, discountCurve)
    return deltaMargin_IR(sensitivities, concentrationThreshold)
    

#Build discount curve ---------------------------------------------------------------------------------------------------------------------------
def get_spot_rates(yieldcurve, dates):
#     keytenors = [0, 6, 12, 18, 24]
    spotDate = yieldcurve.referenceDate()
#     dates = [ql.TARGET().advance(spotDate, t, ql.Months) for t in keytenors ]
    rates = [yieldcurve.zeroRate(t, ql.Actual365Fixed(), ql.Continuous) for t in dates ]
    eq_rate = [rates[d].equivalentRate(ql.Actual365Fixed(), ql.Continuous, ql.Semiannual,\
                                       spotDate , dates[d]).rate() for d in range(len(dates))]
    spots = [eq_r for eq_r in eq_rate]
#     df = pd.DataFrame(list(zip(dates, spots)),columns=["Dates","Rates"], index=['']*len(dates) )
    df = pd.DataFrame(spots,columns=["Rates"], index=None )
    return df, df.plot.line()

#  Attention: Utilisation Temporaire: Construction d'un yieldcurvebuilder nécessaire
def makeEuriborHandle(startDate,  maturity,  fixedLegTenor, index=ql.Euribor6M(), enableExtrapolation = True):
    calendar = ql.TARGET()
    settlementDate = startDate + ql.Period(2, ql.Days)

    # market quotes
    deposits = { (1,ql.Weeks): 0.0382,
             (1,ql.Months): 0.0372,
             (3,ql.Months): 0.0363,
             (6,ql.Months): 0.0353,
             (9,ql.Months): 0.0348,
             (1,ql.Years): 0.0345 }

    swaps = { (2,ql.Years): 0.037125,
          (3,ql.Years): 0.0398,
          (5,ql.Years): 0.0443,
          (10,ql.Years): 0.05165,
          (15,ql.Years): 0.055175 }

    # convert them to Quote objects
    for n,unit in deposits.keys():
        deposits[(n,unit)] = ql.SimpleQuote(deposits[(n,unit)])
    
    for n,unit in swaps.keys():
        swaps[(n,unit)] = ql.SimpleQuote(swaps[(n,unit)])

    dayCounter = ql.Actual360()
    settlementDays = 2
    depositHelpers = [ ql.DepositRateHelper(ql.QuoteHandle(deposits[(n,unit)]),
                                         ql.Period(n,unit), settlementDays,
                                         calendar, ql.ModifiedFollowing,
                                         False, dayCounter)
                       for n, unit in [(1,ql.Weeks),(1,ql.Months),(3,ql.Months),
                                       (6,ql.Months),(9,ql.Months),(1,ql.Years)] ]

    settlementDays = 2
    fixedLegFrequency = fixedLegTenor.frequency()
    fixedLegAdjustment = ql.Unadjusted
    fixedLegDayCounter = ql.Thirty360()
    floatingLegFrequency = fixedLegFrequency
    floatingLegTenor = fixedLegTenor
    floatingLegAdjustment = ql.ModifiedFollowing
    
    swapHelpers = [ ql.SwapRateHelper(ql.QuoteHandle(swaps[(n,unit)]),
                                   ql.Period(n,unit), calendar,
                                   fixedLegFrequency, fixedLegAdjustment,
                                   fixedLegDayCounter, index)
                    for n, unit in swaps.keys() ]
    
#     discountTermStructure = ql.RelinkableYieldTermStructureHandle()
#     forecastTermStructure = ql.RelinkableYieldTermStructureHandle()
    
    helpers = depositHelpers + swapHelpers
    
    depoFraSwapCurve = ql.PiecewiseFlatForward(settlementDate, helpers, ql.Actual360())
    if(enableExtrapolation == True): depoFraSwapCurve.enableExtrapolation()
    
#   end = calendar.advance(settlementDate, maturity)

    return depoFraSwapCurve #, discountTermStructure, forecastTermStructure




