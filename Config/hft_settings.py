from IBridgePy.constants import TraderRunMode

MARKET_MANAGER = {
    'baseFreqOfProcessMessage': 0.25,  # second
}


REPEATER = {
    'slowdownInSecond': 0.25  # second
}

TRADER = {
    'runMode': TraderRunMode.HFT  # run handle_data every second, not run_like_quantopian
}
