# Lido Bond Strategy

This strategy monitors stETH/ETH price divergence and compares the expected returns from using funds from a dry powder buffer to swap ETH to stETH and wait through the withdrawal queue vs a baseline yield from lending (wrapped) stETH on Aave.

## Overview

The strategy monitors three key metrics:
1. **stETH Price**: Current price of stETH in ETH terms from Curve's stETH/ETH pool.
2. **stETH Yield**: Current lending rate for wstETH on Aave.
3. **Withdrawal Queue Duration**: Current wait time for Lido withdrawals.

It calculates two values:
- **Queue Coupon**: Expected value from the stETH/ETH price difference (price - 1) * ETH amount.
- **Reference Coupon**: Expected value from lending on Aave for the withdrawal queue duration, accounting for some risk premium.

When the price of the Queue Coupon exceeds the Reference Coupon, this indicates a potentially profitable opportunity.

### Run the Strategy

   ```bash
   nix develop
   python strategy.py
   ```

### Notes

- More sophisticated accounting of liquidity would significantly improve reliability, but this comes at the cost of complexity and execution speed. Same goes for better volitility estimates.
- Using an exponential moving average for the stETH/ETH price may improve the execution success rate, however there are special considertations for handling this in a zk coprocessor.
- Transaction fee estimates are not included in the calculation.
- Transaction submission logic has not been implemented.
