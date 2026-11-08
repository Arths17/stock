from stockbot.data.congress_house import parse_ptr_text

SAMPLE = """
ID         Owner Asset                                            Transaction Date            Notification Amount
                                                                  Type                        Date
                       GSK plc American Depositary Shares         S                 07/28/2025 08/11/2025             $1,001 - $15,000
                       (GSK) [ST]
                       F      S      : New
SP                     Apple Inc. - Common Stock                  P (partial)       01/02/2025 01:00
 SP    Microsoft Corp                                              P                 03/03/2025 03/20/2025             $15,001 -
       (MSFT) [ST]                                                                                                       $50,000
"""


def test_parses_sell_row_with_wrapped_ticker():
    rows = parse_ptr_text(SAMPLE, "Robert B. Aderholt", "AL04", "20032062", "9/10/2025")
    gsk = [r for r in rows if r["ticker"] == "GSK"][0]
    assert gsk["side"] == "sell"
    assert gsk["transaction_date"] < gsk["notification_date"]
    assert gsk["amount_min"] == 1001 and gsk["amount_max"] == 15000


def test_parses_owner_and_wrapped_amount():
    rows = parse_ptr_text(SAMPLE, "X", "AL04", "1", "9/10/2025")
    msft = [r for r in rows if r["ticker"] == "MSFT"][0]
    assert msft["owner"] == "SP" and msft["side"] == "buy"
    assert msft["amount_max"] == 50000


def test_ignores_rows_without_tickers():
    assert parse_ptr_text("junk line\nmore junk", "X", "Y", "1", "1/1/2025") == []
