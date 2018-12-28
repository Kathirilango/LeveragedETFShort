from quantopian.pipeline import Pipeline,CustomFactor
        
def initialize(context):
    set_commission(commission.PerTrade(cost=5)) 
    set_slippage(slippage.FixedSlippage(spread=0))    
    pipe=Pipeline()
    context.bull=sid(45570)
    context.bear=sid(45571)
    context.target_notional=pow(10,4)   
    schedule_function(allocate,date_rules.every_day(),time_rules.market_close(hours=0,minutes=45))
    schedule_function(record_vars,date_rules.every_day(),time_rules.market_close(hours=0,minutes=45))
    
def record_vars(context,data):
    record(lever=context.account.leverage)
    
def allocate(context,data):
    starting_cash = context.portfolio.starting_cash
    pnl = context.portfolio.pnl
    market_value = starting_cash + pnl
    bet_size = market_value * 1.8
    context.bull_trade_amt=-((0.5*bet_size)/(data.history(context.bull,'price',1,'1m')[0]))-context.portfolio.positions[context.bull].amount
    context.bear_trade_amt=-((0.5*bet_size)/(data.history(context.bear,'price',1,'1m')[0]))-context.portfolio.positions[context.bear].amount
    log.info(('context.bull_trade_amt=%s')%(context.bull_trade_amt))
    log.info(('context.bear_trade_amt=%s')%(context.bear_trade_amt))
    order(context.bull,context.bull_trade_amt)
    order(context.bear,context.bear_trade_amt)