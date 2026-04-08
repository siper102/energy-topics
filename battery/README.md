# Battery Dispatch Optimization

This project implements a microgrid dispatch optimizer for a stationary battery storage system. It solves a Finite-Horizon Discrete-Time Optimal Control Problem to determine the optimal power dispatch over a specific horizon.

## Project Goal
The primary goal is to minimize total operational costs, which include:
- Net grid energy exchange costs (buying and selling electricity).
- A non-linear penalty term representing battery cycle degradation (modeled as a quadratic function of charge/discharge power).

The optimizer accounts for system constraints such as battery capacity limits, maximum charge/discharge power, conversion efficiencies, and power node balance (integrating solar PV generation and household load).

## TODO
- [ ] Add data source for solar and load
- [ ] Check model behavior
