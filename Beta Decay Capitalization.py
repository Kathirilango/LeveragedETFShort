from quantopian.pipeline import Pipeline,CustomFactor
        
def initialize(context):
    context.bull=symbol('jnug')
    context.bear=symbol('jdst')
    schedule_function(allocate,date_rules.every_day(),time_rules.market_open(hours=3.5,minutes=0),half_days=True)
    schedule_function(record_vars,date_rules.every_day(),time_rules.market_close(hours=0,minutes=1),half_days=True)
    
def record_vars(context,data):   
    lever=context.account.leverage
    # bull_perc=abs((context.portfolio.positions[context.bull].amount*(data.current(context.bull,'price')))/(context.portfolio.portfolio_value*lever))*100
    # bear_perc=abs((context.portfolio.positions[context.bear].amount*(data.current(context.bear,'price')))/(context.portfolio.portfolio_value*lever))*100
    
    #write intended leverage ratio below for log generation
    if lever>1.0:
        log.warn('Leverage Exceeded: '+str(lever))
    #record(pos_spread=abs(bull_perc-bear_perc))
    record(leverage=lever)

def allocate(context,data):
    #edit leverage below (usually intended leverage ratio-0.1)
    leverage=0.9
    bet_size = context.portfolio.portfolio_value * leverage
    context.bull_trade_amt=-((0.5*bet_size)/(data.current(context.bull,'price')))-context.portfolio.positions[context.bull].amount
    context.bear_trade_amt=-((0.5*bet_size)/(data.current(context.bear,'price')))-context.portfolio.positions[context.bear].amount
    order(context.bull,context.bull_trade_amt)
    order(context.bear,context.bear_trade_amt)
    
def handle_data(context,data):
    lever=context.account.leverage
    try:
        bull_perc=abs((context.portfolio.positions[context.bull].amount*(data.current(context.bull,'price')))/(context.portfolio.portfolio_value*lever))*100
        bear_perc=abs((context.portfolio.positions[context.bear].amount*(data.current(context.bear,'price')))/(context.portfolio.portfolio_value*lever))*100
        pos_spread=abs(bull_perc-bear_perc)
        
#edit number (5) below for managing spread
        if pos_spread>5:
            allocate(context,data)
    except:
        pass