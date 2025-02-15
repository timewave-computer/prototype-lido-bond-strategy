import time
import json
import traceback
import signal
import math
from web3 import Web3

# Web3 connection
WEB3_PROVIDER_URL = "https://mainnet.infura.io/v3/timewave"
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER_URL))

# Contract addresses
CURVE_SWAP_POOL_ADDRESS = Web3.to_checksum_address("0x21e27a5e5513d6e65c4f830167390997aa84843a")    # Curve stETH/ETH pool
AAVE_LENDING_POOL_ADDRESS = Web3.to_checksum_address("0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2")  # Aave v3 lending pool
WSTETH_TOKEN_ADDRESS = Web3.to_checksum_address("0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0")       # wstETH token
LIDO_QUEUE_ADDRESS = Web3.to_checksum_address("0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1")         # Lido withdrawals

# Strategy parameters
ETH_DRY_POWDER = 1                        # Amount of ETH to simulate
RISK_PREMIUM = 50 / 10000                 # 50 bps premium for illiquidity and rate volatility
POLL_INTERVAL = 2                         # Seconds between RPC requests

# Constants
RAY = 10**27                             # Aave rate precision
ETH_TO_WEI = 10**18                      # ETH/WEI conversion
SECONDS_PER_YEAR = 365 * 24 * 60 * 60
YEARS_PER_SECOND = 1 / SECONDS_PER_YEAR

# Load contract ABIs
with open("abis/curve_abi.json") as f:
    curve_abi = json.load(f)
with open("abis/aave_abi.json") as f:
    aave_abi = json.load(f)
with open("abis/lido_abi.json") as f:
    lido_abi = json.load(f)

# Initialize contract instances
curve_contract = w3.eth.contract(address=CURVE_SWAP_POOL_ADDRESS, abi=curve_abi)
aave_contract = w3.eth.contract(address=AAVE_LENDING_POOL_ADDRESS, abi=aave_abi)
lido_contract = w3.eth.contract(address=LIDO_QUEUE_ADDRESS, abi=lido_abi)

def get_curve_steth_price():
    """Fetch stETH price from Curve pool."""
    try:
        # Get price from Curve get_dy function (amount of ETH received for 1 stETH)
        steth_price = curve_contract.functions.get_dy(1, 0, ETH_TO_WEI).call() / ETH_TO_WEI
        print(f"stETH/ETH Price:      {steth_price:.6f}")
        return steth_price
    
    except Exception as e:
        print(f"Error getting stETH price from Curve contract at {CURVE_SWAP_POOL_ADDRESS}: {e}")
        traceback.print_exc()
        return 0

def get_aave_steth_yield():
    """Fetch wstETH interest rates from Aave."""
    try:
        # Get wstETH yield from Aave reserve data
        reserve_data = aave_contract.functions.getReserveData(WSTETH_TOKEN_ADDRESS).call()
        current_liquidity_rate = reserve_data[2]  # Index 2 is currentLiquidityRate
        
        # Convert from RAY to APY using Aave's formula:
        # APY = ((1 + ((liquidityRate / 10**27) / 31536000)) ^ 31536000) - 1
        normalized_rate = current_liquidity_rate / RAY
        rate_per_second = normalized_rate / SECONDS_PER_YEAR
        apy_decimal_year = (1 + rate_per_second) ** SECONDS_PER_YEAR - 1
        
        print(f"Supply APY:           {apy_decimal_year*100:.4f}%")
        return apy_decimal_year

    except Exception as e:
        print(f"Error getting wstETH interest rates from Aave contract at {AAVE_LENDING_POOL_ADDRESS}: {e}")
        traceback.print_exc()
        return 0

def get_lido_steth_withdraw_duration():
    """Fetch Lido withdrawal queue duration."""
    try:
        # Get the latest withdrawal request ID
        last_request_id = lido_contract.functions.getLastRequestId().call()
        
        if last_request_id == 0:
            print("Withdrawal Queue:     Empty")
            return 0

        # Get current block timestamp and last request status
        current_timestamp = w3.eth.get_block('latest')['timestamp']
        status = lido_contract.functions.getWithdrawalStatus([last_request_id]).call()[0]
        last_request_timestamp = status[3]  # Index 3 is timestamp
        
        # Calculate queue duration in years
        queue_duration_seconds = current_timestamp - last_request_timestamp          
        queue_duration_years = queue_duration_seconds * YEARS_PER_SECOND
        print(f"Withdrawal Queue:     {queue_duration_years:.4f} years")
        
        return queue_duration_years
        
    except Exception as e:
        print(f"Error getting stETH withdrawal duration from Lido contract at {LIDO_WITHDRAWAL_QUEUE_ADDRESS}: {e}")
        traceback.print_exc()
        return 0

def main():
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        try:
            divider = "-" * 37  # Divider length
            print(f"\n{divider}")
            print(f"Block Number:         {w3.eth.block_number}")
            
            # Fetch current market data
            steth_price = get_curve_steth_price()                         # Price in ETH
            steth_yield = get_aave_steth_yield()                          # APY as decimal
            steth_withdraw_duration = get_lido_steth_withdraw_duration()  # Years

            # Calculate arbitrage opportunity
            net_yield = steth_yield - RISK_PREMIUM
            steth_reference_coupon = steth_withdraw_duration * net_yield * ETH_DRY_POWDER
            steth_queue_coupon = (steth_price - 1) * ETH_DRY_POWDER
            
            print(f"Reference Coupon:    {steth_reference_coupon:>9.6f} ETH")
            print(f"Queue Coupon:        {steth_queue_coupon:>9.6f} ETH")

            # Check profitability
            relative_profit = steth_queue_coupon - steth_reference_coupon
            if relative_profit > 0:
                print(f"Result:              +{relative_profit:>8.6f} ETH 💰")
            else:
                print(f"Result:              {relative_profit:>9.6f} ETH 💸")
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            traceback.print_exc()
        
        print(divider)
        time.sleep(POLL_INTERVAL)

def signal_handler(signum, frame):
    print("\nExiting...")
    exit(0)

if __name__ == "__main__":
    main()
