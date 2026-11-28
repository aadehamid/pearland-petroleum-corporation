// Quint formal specification for PO-01: Tank Control-Volume Bounds & Exact Crossing Split
// Governing specifications: PPC-REVIEW-002 EQ-02, PPC-REVIEW-004 PO-01, ADR-0050
module po01_tank_bounds {
  pure val MIN_BBL = 1000
  pure val MAX_BBL = 12000

  var stock_bbl: int
  var diverted_bbl: int
  var total_in_bbl: int
  var total_out_bbl: int
  var opening_bbl: int

  action init = all {
    stock_bbl' = 10000,
    opening_bbl' = 10000,
    diverted_bbl' = 0,
    total_in_bbl' = 0,
    total_out_bbl' = 0,
  }

  // Exact intra-step split: never clip end-of-step; excess over MAX_BBL diverts cleanly
  action step_transfer(in_req: int, out_req: int): bool = {
    val unclamped = stock_bbl + in_req - out_req
    val accepted_in =
      if (unclamped > MAX_BBL) MAX_BBL - stock_bbl + out_req
      else in_req
    val accepted_out =
      if (unclamped < MIN_BBL) stock_bbl + in_req - MIN_BBL
      else out_req
    val div = (in_req - accepted_in) + (out_req - accepted_out)
    all {
      in_req >= 0,
      out_req >= 0,
      accepted_in >= 0,
      accepted_out >= 0,
      stock_bbl' = stock_bbl + accepted_in - accepted_out,
      total_in_bbl' = total_in_bbl + accepted_in,
      total_out_bbl' = total_out_bbl + accepted_out,
      diverted_bbl' = diverted_bbl + div,
      opening_bbl' = opening_bbl,
    }
  }

  action step = {
    nondet in_req = 0.to(1500).oneOf()
    nondet out_req = 0.to(1500).oneOf()
    step_transfer(in_req, out_req)
  }

  val inv_bounds = stock_bbl >= MIN_BBL and stock_bbl <= MAX_BBL
  val inv_conservation = stock_bbl == opening_bbl + total_in_bbl - total_out_bbl
  val inv_nonneg_diverted = diverted_bbl >= 0
  val safety_all = inv_bounds and inv_conservation and inv_nonneg_diverted
}
