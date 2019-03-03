from quantopian.pipeline import Pipeline,CustomFactor
import numpy as np
import operator
from collections import OrderedDict
        
def initialize(context):
    context.bull=""
    context.bear=""
    context.underlying = ""
    context.universe = {
        symbol('GDXJ'): {'bull':symbol('JNUG'), 'bear':symbol('JDST')},
        symbol('FCG'):  {'bull':symbol('GASL'), 'bear':symbol('GASX')},
        symbol('XBI'):  {'bull':symbol('LABU'), 'bear':symbol('LABD')},
        #symbol('XSD'):  {'bull':symbol('SOXL'), 'bear':symbol('SOXS')},
        symbol('XOP'):  {'bull':symbol('GUSH'), 'bear':symbol('DRIP')},
        #symbol('XLC'):  {'bull':symbol('TAWK'), 'bear':symbol('MUTE')},
        #symbol('XLY'):  {'bull':symbol('WANT'), 'bear':symbol('PASS')},
        #symbol('XLP'):  {'bull':symbol('NEED'), 'bear':symbol('LACK')},
        symbol('XLE'):  {'bull':symbol('ERX'),  'bear':symbol('ERY')},
        symbol('XLF'):  {'bull':symbol('FAZ'),  'bear':symbol('FAS')},
        symbol('GDX'):  {'bull':symbol('NUGT'), 'bear':symbol('DUST')},
        symbol('XLRE'): {'bull':symbol('DRN'),  'bear':symbol('DRV')},
        symbol('XLK'):  {'bull':symbol('TECL'), 'bear':symbol('TECS')},
        symbol('TYBS'): {'bull':symbol('TMF'),  'bear':symbol('TMV')},
        symbol('TYNS'): {'bull':symbol('TYD'),  'bear':symbol('TYO')},
        symbol('FXI'):  {'bull':symbol('YINN'), 'bear':symbol('YANG')},
        symbol('EFA'):  {'bull':symbol('DZK'),  'bear':symbol('DPK')},
        symbol('EEM'):  {'bull':symbol('EDC'),  'bear':symbol('EDZ')},
        symbol('ERUS'): {'bull':symbol('RUSL'), 'bear':symbol('RUSS')},
        symbol('IJH'):  {'bull':symbol('MIDU'), 'bear':symbol('MIDZ')},
        symbol('SPY'):  {'bull':symbol('SPXL'), 'bear':symbol('SPXS')},
        #symbol('IWM'):  {'bull':symbol('TNA'),  'bear':symbol('TNZ')}
    }
        
    context.is_security = {symbol('GDXJ'): False, symbol('FCG'): False, symbol('XBI'): False, symbol('XSD'): False, symbol('XOP'): False, symbol('XLE'): False, symbol('XLF'): False, symbol('GDX'): False, symbol('XLRE'): False, symbol('XLK'): False, symbol('TYBS'): False, symbol('TYNS'): False, symbol('FXI'): False, symbol('EFA'): False, symbol('EEM'): False, symbol('ERUS'): False, symbol('IJH'): False, symbol('SPY'): False}
    
    #insert interactive brokers commission below
    set_commission(commission.PerShare(cost=0.0035, min_trade_cost=0.35))
    set_slippage(slippage.FixedSlippage(spread=0.00))
    #insert intended leverage below
    context.truleverage=3
    #insert max imbalance below
    context.trupos_spread=10
    context.empty=True
    context.universe_size = len(context.universe)
    context.num_securities = 2
    context.min_volatility = 0
    schedule_function(EOD,date_rules.every_day(),time_rules.market_close(hours=0,minutes=3),half_days=True) 
    schedule_function(select_securities, date_rules.every_day(), time_rules.market_open(hours=0, minutes=1))
    
def EOD(context,data): 
    #record(imbalance=context.pos_spread)
    record(leverage=context.account.leverage)
    context.open_orders = get_open_orders()
    if context.open_orders:
        for orders,_ in context.open_orders.iteritems():
            cancel_order(orders)
    context.empty=True
    print("EOD")
    #context.eod = True
    #r_value=np.corrcoef(context.volatility,context.performance)
    #corr=(r_value[0][1])**2
    #record(corr=corr)
    #print(corr)
    
def warn_leverage(context, data):
    log.warn('Leverage Exceeded: '+str(context.account.leverage))
    context.open_orders = get_open_orders()
    if context.open_orders:
        for orders,_ in context.open_orders.iteritems():
            cancel_order(orders)
    for equity in context.portfolio.positions:  
        order_target_percent(equity, 0)
    context.empty = True    
    
def select_securities(context, data):
    
    context.rolling_volatility={}   
    for security in context.universe:
        price_history = data.history(security,"price",20,"1d")
        rolling_vol = compute_volatility(context,price_history)
        context.rolling_volatility[security] = rolling_vol
        
    context.rolling_volatility = OrderedDict(sorted(context.rolling_volatility.items(), key=lambda kv: kv[1], reverse=True))
    print(context.rolling_volatility)
    
    context.securities = {}
    below_limit = 0
    for i in range(context.num_securities):
        underlying = context.rolling_volatility.keys()[i]
        if (context.rolling_volatility[underlying] < context.min_volatility):
            below_limit += 1
            continue
        
        bull = context.universe[underlying]['bull']
        bear = context.universe[underlying]['bear']
        
        context.securities[underlying] = {}
        context.securities[underlying]['bull'] = bull
        context.securities[underlying]['bear'] = bear
        context.is_security[underlying] = True
    
    for i in range (context.num_securities-below_limit, context.universe_size):
        underlying = context.rolling_volatility.keys()[i]
        if (context.is_security[underlying]):
            order_target_percent(context.universe[underlying]['bull'], 0)
            order_target_percent(context.universe[underlying]['bear'], 0)
            context.is_security[underlying] = False
            
    print( context.securities)
    context.rolling_volatility = dict(context.rolling_volatility)
    
def EOQ(context,data):
    #print (context.rolling_volatility)
    context.rv_sum = 0
    for security in context.securities:
        context.rv_sum += context.rolling_volatility[security]
    for security in context.securities:
        context.bull = context.securities[security]['bull']
        context.bear = context.securities[security]['bear']
        context.underlying = security
        allocate(context, data)
    #print(context.portfolio.positions)
    

def compute_volatility(context,price_history):  
    daily_returns = price_history.pct_change().dropna().values  
    historical_vol_daily = np.std(daily_returns,axis=0)
    #record(volatility=historical_vol_daily*1000)  
    return historical_vol_daily

def get_pair_value(context, data):
    pair_value = context.portfolio.portfolio_value*context.rolling_volatility[context.underlying]/context.rv_sum
    return pair_value
    
def is_pair_tradable(context, data):
    return (data.can_trade(context.bull) and data.can_trade(context.bear))
    
def allocate(context,data):
    context.open_orders = get_open_orders()
    if context.open_orders:
        for orders,_ in context.open_orders.iteritems():
            cancel_order(orders)
            
    bet_size = get_pair_value(context, data) * (context.truleverage-0.2)
    bull_trade_amt=-((0.5*bet_size)/(data.current(context.bull,'price')))-context.portfolio.positions[context.bull].amount
    bear_trade_amt=-((0.5*bet_size)/(data.current(context.bear,'price')))-context.portfolio.positions[context.bear].amount
    
    print( str(context.bull) + " TA: " + str(bull_trade_amt) + " at " + str(data.current(context.bull,'price')) + " per share, currently have " + str(context.portfolio.positions[context.bull].amount) + " shares")
    print(str(context.bear) + " TA: " + str(bear_trade_amt)+ " at " + str(data.current(context.bear,'price')) + " per share, currently have " + str(context.portfolio.positions[context.bear].amount) + " shares")
    
    if (is_pair_tradable(context, data)):
        bull_below_limit = bull_trade_amt*data.current(context.bull,'price') < (0.5*context.truleverage*context.portfolio.portfolio_value)
        bear_below_limit = bear_trade_amt*data.current(context.bear,'price') < (0.5*context.truleverage*context.portfolio.portfolio_value)
        if (bull_below_limit and bear_below_limit):
            order(context.bull,bull_trade_amt)
            order(context.bear,bear_trade_amt)
            context.empty=False
        else:
            warn_leverage(context, data)
        
def handle_data(context,data):
    
    context.open_orders = get_open_orders()
    if context.open_orders:
        return
    
    if context.empty==False:
        for security in context.securities.keys():
            context.bull = context.securities[security]['bull']
            context.bear = context.securities[security]['bear']
            context.underlying = security
            pair_value = get_pair_value(context, data)

            bull_perc=abs((context.portfolio.positions[context.bull].amount*(data.current(context.bull,'price')))/pair_value)*100
            bear_perc=abs((context.portfolio.positions[context.bear].amount*(data.current(context.bear,'price')))/pair_value)*100
            context.pos_spread=abs(bull_perc-bear_perc)

            if context.pos_spread>context.trupos_spread and not (context.exchange_time.hour == 9 and context.exchange_time.minute < 40):
                print ("ALLOCATING SPREAD")
                allocate(context, data)       
    if context.account.leverage>context.truleverage or context.account.leverage < 0:
        warn_leverage(context, data)
        
    context.exchange_time = get_datetime('US/Eastern')
    if context.empty==True and not (context.exchange_time.hour == 15 and context.exchange_time.minute > 57) and not context.exchange_time.hour == 16 and not (context.exchange_time.hour == 9 and context.exchange_time.minute < 32):
        #print("ALLOCATING EOQ")
        EOQ(context,data)
