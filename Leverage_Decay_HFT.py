from quantopian.pipeline import Pipeline,CustomFactor
        
def initialize(context):
    context.bull=symbol('jnug')
    context.bear=symbol('jdst')
    context.lever=context.account.leverage
    #insert intended leverage below
    context.truleverage=1
    schedule_function(record_vars,date_rules.every_day(),time_rules.market_close(hours=0,minutes=1),half_days=True)
    
def record_vars(context,data): 
    record(leverage=context.lever)
    if context.lever>context.truleverage:
        log.warn('Leverage Exceeded: '+str(context.lever))        

def allocate(context,data):
    bet_size = context.portfolio.portfolio_value * (context.truleverage-0.2)
    context.bull_trade_amt=-((0.5*bet_size)/(data.current(context.bull,'price')))-context.portfolio.positions[context.bull].amount
    context.bear_trade_amt=-((0.5*bet_size)/(data.current(context.bear,'price')))-context.portfolio.positions[context.bear].amount
    order(context.bull,context.bull_trade_amt)
    order(context.bear,context.bear_trade_amt)
    
def handle_data(context,data):
    try:
        allocate(context,data)
    except:
        pass