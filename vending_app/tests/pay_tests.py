import pytest

from ..views import pay
tab_185 = [1,1,1,1,1]

@pytest.mark.parametrize("coin_table,ammount_to_pay,expected,ret", [
    ([1,1,1,1,1], 120, [1,1,0,1,0],0),
    ([1,1,1,1,1], 185, [0,0,0,0,0],0),
    ([1,1,1,1,1], 200, [0,0,0,0,0],15),
])
def test_pay(coin_table, ammount_to_pay, expected,ret):
    _ret = pay(coin_table,ammount_to_pay)
    assert coin_table == expected
    assert _ret == ret

def test_pay_insuff_200():
    coins_tab = tab_185[:] # get 185 tab
    ret = pay(coins_tab,200)
    assert coins_tab == [0,0,0,0,0]
    assert ret == 15

def test_pay_give_change():
    coins_tab = [0,0,0,0,2] # 200
    ret = pay(coins_tab,105)
    assert coins_tab == [1,0,2,1,0]
    assert ret == 0
