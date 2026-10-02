# PPC-REG-003 --- KPI, Metric, and Data Product Register

**Purpose:** Seed inventory for governed performance and reusable
products.

## Data products

  ----------------------------------------------------------------------------
  Product                 Type                         Main purpose
  ----------------------- ---------------------------- -----------------------
  Event                   Foundational/cross-cutting   normalized events and
                                                       exposure metadata

  Market & Pricing        Foundational/derived         market observations,
                                                       spreads, regional
                                                       context

  Asset & Reliability     Foundational                 asset/unit availability
                                                       and production
                                                       capability

  Physical Movement &     Foundational/derived         shipments, routes,
  Logistics                                            freight, ETA, execution

  Commercial Margin       Derived                      theoretical/realized
                                                       margin and leakage

  Commercial Risk         Derived                      positions, event
                                                       exposure,
                                                       margin-at-risk

  Forecast Performance    Derived                      forecast, actual, error
                                                       and bias
  ----------------------------------------------------------------------------

## Initial KPI candidates

  -----------------------------------------------------------------------
  KPI                     Area                    Typical drivers
  ----------------------- ----------------------- -----------------------
  Gasoline Netback CPG    Commercial              market price, cost,
                                                  freight, pricing

  ULSD Netback CPG        Commercial              diesel market,
                                                  production, freight,
                                                  spot replacement

  Margin Capture %        Enterprise/Commercial   downtime, yield,
                                                  logistics, pricing,
                                                  hedging

  Trading P&L             Trading                 positions, prices,
                                                  execution

  Optionality Capture     Trading                 chosen vs feasible
                                                  alternatives

  OTIF                    Logistics               shipment timing,
                                                  inventory, route
                                                  capacity

  Logistics Cost/Gallon   Logistics               freight, fuel,
                                                  congestion, mode

  Demurrage Cost          Logistics               delay and contractual
                                                  terms

  Refinery Utilization    Refining                throughput/available
                                                  capacity

  Unplanned Capacity Loss Refining                outages and rate
                                                  reductions

  Yield Capture           Refining                actual vs reference
                                                  yield

  Forecast Accuracy       Planning                forecast vs actual

  Inventory Days of Cover Planning                inventory and forecast
                                                  demand

  Margin-at-Risk          Risk                    scenario exposure

  Position Exposure       Risk                    trades, inventory,
                                                  commitments, hedges
  -----------------------------------------------------------------------

## Classification rule

Measurements become metrics when standardized for repeatable
monitoring/diagnosis. Only a governed subset becomes KPI after
objective, owner, formula, grain, target/evaluation, cadence and action
are defined.
