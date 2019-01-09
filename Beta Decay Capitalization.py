from quantopian.pipeline import Pipeline,CustomFactor
        
def initialize(context):
    context.bull=symbol('jnug')
    context.bear=symbol('jdst')
    schedule_function(allocate,date_rules.every_day(),time_rules.market_close(hours=1,minutes=0))
    schedule_function(record_vars,date_rules.every_day(),time_rules.market_close(hours=0,minutes=1))
    
def record_vars(context,data):
    lever=context.account.leverage
    #uncomment to record leverage
    #record(lever=context.account.leverage)
    bull_perc=abs((context.portfolio.positions[context.bull].amount*data.history(context.bull,'price',1,'1m')[0])/(context.portfolio.portfolio_value*lever))*100
    bear_perc=abs((context.portfolio.positions[context.bear].amount*data.history(context.bear,'price',1,'1m')[0])/(context.portfolio.portfolio_value*lever))*100
    #comment line below to record leverage
    record(pos_spread=abs(bull_perc-bear_perc))
    log.info('bull percentage=%s'%(bull_perc))
    log.info('bear percentage=%s'%(bear_perc))
    
def allocate(context,data):
    leverage=3.9
    bet_size = context.portfolio.portfolio_value * leverage
    context.bull_trade_amt=-((0.5*bet_size)/(data.history(context.bull,'price',1,'1m')[0]))-context.portfolio.positions[context.bull].amount
    context.bear_trade_amt=-((0.5*bet_size)/(data.history(context.bear,'price',1,'1m')[0]))-context.portfolio.positions[context.bear].amount
    order(context.bull,context.bull_trade_amt)
    order(context.bear,context.bear_trade_amt)