from quantopian.pipeline import Pipeline,CustomFactor
        
def initialize(context):
    context.bull=symbol('jnug')
    context.bear=symbol('jdst')
    schedule_function(allocate,date_rules.every_day(),time_rules.market_close(hours=1,minutes=0))
    schedule_function(record_vars,date_rules.every_day(),time_rules.market_close(hours=0,minutes=1))
    
def record_vars(context,data):
    record(lever=context.account.leverage)
    
def allocate(context,data):
    bet_size = context.portfolio.portfolio_value * 3.9
    context.bull_trade_amt=-((0.5*bet_size)/(data.history(context.bull,'price',1,'1m')[0]))-context.portfolio.positions[context.bull].amount
    context.bear_trade_amt=-((0.5*bet_size)/(data.history(context.bear,'price',1,'1m')[0]))-context.portfolio.positions[context.bear].amount
    log.info(('context.bull_trade_amt=%s')%(context.bull_trade_amt))
    log.info(('context.bear_trade_amt=%s')%(context.bear_trade_amt))
    order(context.bull,context.bull_trade_amt)
    order(context.bear,context.bear_trade_amt)