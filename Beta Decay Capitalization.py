from quantopian.pipeline import Pipeline,CustomFactor
import numpy as np
        
def initialize(context):
    context.bull=symbol('jnug')
    context.bear=symbol('jdst')
    #context.underlying=symbol('gdxj')
    context.securities = {
        symbol('GDXJ'): {'bull':symbol('JNUG'), 'bear':symbol('JDST')},
        symbol('FCG'):  {'bull':symbol('GASL'), 'bear':symbol('GASX')},
        symbol('XBI'):  {'bull':symbol('LABU'), 'bear':symbol('LABD')},
        symbol('SOXX'): {'bull':symbol('SOXL'), 'bear':symbol('SOXS')},
        symbol('XOP'):  {'bull':symbol('GUSH'), 'bear':symbol('DRIP')},
        #symbol('R1RGSFS'): {'bull':symbol('FAS'),  'bear':symbol('FAZ')},
        #symbol('IXT'): {'bull':symbol('TECL'),  'bear':symbol('TECS')}
    }
    context.lever=context.account.leverage
    #insert interactive brokers commission below
    set_commission(commission.PerShare(cost=0.0035, min_trade_cost=0.35))
    set_slippage(slippage.FixedSlippage(spread=0.00))
    #insert intended leverage below
    context.truleverage=1
    #insert max imbalance below
    context.trupos_spread=10
    context.x=True
    context.open_orders = get_open_orders()  
    context.exchange_time = get_datetime('US/Eastern')
    #context.performance=[]
    #context.volatility=[]
    schedule_function(EOD,date_rules.every_day(),time_rules.market_close(hours=0,minutes=3),half_days=True)
    #run at the end of every 30 days
    #schedule_function(EOQ,date_rules.every_day(),time_rules.market_close(hours=0,minutes=1),half_days=True)
    schedule_function(EOQ,date_rules.month_end(),time_rules.market_close(minutes=30),half_days=True)
    
def EOD(context,data): 
    #record(imbalance=context.pos_spread)
    record(leverage=context.account.leverage)
    if context.open_orders:
        for orders in context.open_orders.iteritemts():
            cancel_order(orders)
    for equity in context.portfolio.positions:  
        order_percent(equity, 0)
    context.x=True
    #r_value=np.corrcoef(context.volatility,context.performance)
    #corr=(r_value[0][1])**2
    #record(corr=corr)
    #print(corr)
    
# def EOQ(context,data):
#     price_history = data.history(context.underlying,"price",23400,"1m")
#     compute_volatility(context,price_history)

# def compute_volatility(context,price_history):  
#     # Compute daily returns  
#     daily_returns = price_history.pct_change().dropna().values  
#     # Compute daily volatility  
#     historical_vol_daily = np.std(daily_returns,axis=0)
#     #returns = context.portfolio.returns
#     #context.performance.append(returns)
#     context.volatility.append(historical_vol_daily)
#     #record(volatility=historical_vol_daily*1000)    

def EOQ(context,data):
    context.rolling_volatility={}
    this_month = get_datetime('US/Eastern').month  
    if this_month in [3, 6, 9, 12]: 
        for security in context.securities:
            price_history = data.history(security,"price",23400,"1m")
            rolling_vol = compute_volatility(context,price_history)
            context.rolling_volatility[security] = rolling_vol
        context.rolling_volatility = sorted(context.rolling_volatility.items(), key=operator.itemgetter(1), reverse=True)
        #print(context.rolling_volatility)
    else:
        return

def compute_volatility(context,price_history):  
    # Compute daily returns  
    daily_returns = price_history.pct_change().dropna().values  
    # Compute daily volatility  
    historical_vol_daily = np.std(daily_returns,axis=0)
    #returns = context.portfolio.returns
    #context.performance.append(returns)
    #context.volatility.append(historical_vol_daily)
    #record(volatility=historical_vol_daily*1000)  
    return historical_vol_daily
    
def allocate(context,data):
    if context.open_orders:
        for orders in context.open_orders.iteritemts():
            cancel_order(orders)
    bet_size = context.portfolio.portfolio_value * (context.truleverage-0.2)
    context.bull_trade_amt=-((0.5*bet_size)/(data.current(context.bull,'price')))-context.portfolio.positions[context.bull].amount
    context.bear_trade_amt=-((0.5*bet_size)/(data.current(context.bear,'price')))-context.portfolio.positions[context.bear].amount
    order(context.bull,context.bull_trade_amt)
    order(context.bear,context.bear_trade_amt)
    context.x=False
        
def handle_data(context,data):
    if len(context.portfolio.positions) > 0:
        bull_perc=abs((context.portfolio.positions[context.bull].amount*(data.current(context.bull,'price')))/(context.portfolio.portfolio_value))*100
        bear_perc=abs((context.portfolio.positions[context.bear].amount*(data.current(context.bear,'price')))/(context.portfolio.portfolio_value))*100
        context.pos_spread=abs(bull_perc-bear_perc)
    if context.lever>context.truleverage:
            log.warn('Leverage Exceeded: '+str(context.lever))
            for equity in context.portfolio.positions:  
                 order_percent(equity, 0)
            context.x=True
    if context.x==True and context.exchange_time.minute<57:
        allocate(context,data)
    try:
        if context.pos_spread>context.trupos_spread:
            allocate(context,data)
    except:
        pass
