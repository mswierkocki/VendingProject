from .models import VALID_COINS

def pay(coin_tab,amount_to_pay):
  assert amount_to_pay%VALID_COINS[0] == 0
  if amount_to_pay<0:
       amount_to_pay*=-1
  for idx in range(0,len(VALID_COINS))[::-1]:
     nominal=VALID_COINS[idx]
     if amount_to_pay>=nominal:
        nc = coin_tab[idx] #nominal coins
        while amount_to_pay>=nominal and coin_tab[idx]>0: # do this wile ammount is greater than nominal and we still have coins
          amount_to_pay-=nominal
          coin_tab[idx]-=1
  if amount_to_pay== 0: #great we payed all no change needed
    return amount_to_pay
  #hence we need to get rest, and we are assured that 1. we have enought to pay, 2. machine has infinte change ;) if we dont have infinite, than we should look for avaiable nominal coins in machine and transfer corespondling to the buyer, or say sorry, no change left.
  # lookup for left coins, at this point we could get any bigger nominal and exchange it all to 5's as a rest, buyt we will
  for idx in range(1,len(VALID_COINS)): # we can't change from 5's
    if coin_tab[idx]>0: # we have some coins and we didnt spend them on amount_to_pay, so amount_to_pay<nominal
       nominal=VALID_COINS[idx]
       if not amount_to_pay<nominal:
         raise Exception('Sanity is broken') # sanity check
       coin_tab[idx]-=1
       nominal-=amount_to_pay
       amount_to_pay-=VALID_COINS[idx]
       # nominal now hold's rest we must add to buyer table
       for idx in range(0,len(VALID_COINS)-1)[::-1]: # we cant add rest in 100's
         coin_nominal=VALID_COINS[idx]
         while nominal>=coin_nominal:
            coin_tab[idx]+=1
            nominal-=coin_nominal
            amount_to_pay+=coin_nominal
  return amount_to_pay

def aquire(ammount :int) -> list:
    """
    Gredy way of getting coins tab, designed for basic functional and testing
    ammount must be multiplication by lowest valid coin!

    Args:
        ammount (int): amount for we generate table

    Raises:
        Exception: When math breaks

    Returns:
        list: requested COIN_TAB reprezenting ammount in valid coins
    """
    assert ammount%VALID_COINS[0] == 0
    if ammount<0:
       ammount*=-1
    ret = []
    for idx in range(0,len(VALID_COINS))[::-1]:
      nominal=VALID_COINS[idx]
      nc = 0 # coins to add with current nominal
      while ammount>=nominal: # do this wile ammount is greater than nominal
          ammount-=nominal
          nc+=1
      ret.append(nc)
    if ammount!= 0:
        raise Exception("Aquire is insane!")    
    return ret[::-1]