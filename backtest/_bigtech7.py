from testbed import zero_weights
BASKET = ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA"]
def strategy(observation):
    port = observation["portfolio"]
    if bool(port.get("positions")) or sum((port.get("weights") or {}).values()) > 0:
        return None
    if observation["round"]["number"] != 1:
        return None
    out = zero_weights(); out.update({s: 0.25 / 7 for s in BASKET}); return out
