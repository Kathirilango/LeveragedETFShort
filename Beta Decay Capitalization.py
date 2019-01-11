from quantopian.pipeline import Pipeline,CustomFactor
        
def initialize(context):
    context.bull=symbol('jnug')
    context.bear=symbol('jdst')
    context.lever=context.account.leverage
    #insert intended leverage below
    context.truleverage=4
    #insert max imbalance below
    context.trupos_spread=5
    
    schedule_function(allocate,date_rules.every_day(),time_rules.market_open(hours=3.5,minutes=0),half_days=True)
    schedule_function(record_vars,date_rules.every_day(),time_rules.market_close(hours=0,minutes=1),half_days=True)
    
def record_vars(context,data): 
    try:
        bull_perc=abs((context.portfolio.positions[context.bull].amount*(data.current(context.bull,'price')))/(context.portfolio.portfolio_value*context.lever))*100
        bear_perc=abs((context.portfolio.positions[context.bear].amount*(data.current(context.bear,'price')))/(context.portfolio.portfolio_value*context.lever))*100
        context.pos_spread=abs(bull_perc-bear_perc)
        if context.lever>context.truleverage:
            log.warn('Leverage Exceeded: '+str(context.lever))
        record(imbalance=context.pos_spread)
        record(leverage=context.lever)
    except:
        pass

def allocate(context,data):
    bet_size = context.portfolio.portfolio_value * (context.truleverage-0.1)
    context.bull_trade_amt=-((0.5*bet_size)/(data.current(context.bull,'price')))-context.portfolio.positions[context.bull].amount
    context.bear_trade_amt=-((0.5*bet_size)/(data.current(context.bear,'price')))-context.portfolio.positions[context.bear].amount
    order(context.bull,context.bull_trade_amt)
    order(context.bear,context.bear_trade_amt)
    
def handle_data(context,data):
    try:
        if context.pos_spread>context.trupos_spread:
            allocate(context,data)
    except:
        pass