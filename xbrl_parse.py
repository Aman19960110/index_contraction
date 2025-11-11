from bs4 import BeautifulSoup
import requests
import pandas as pd
from lxml import etree
from io import BytesIO

def parse_xbrl_shareholding(url: str) -> pd.DataFrame:
    """
    Parse NSE XBRL Shareholding Pattern XML and return a clean DataFrame
    containing category-wise shareholding details.

    Parameters
    ----------
    url : str
        XBRL XML URL (e.g., 'https://nsearchives.nseindia.com/corporate/xbrl/SHP_XXXX_WEB.xml')

    Returns
    -------
    pd.DataFrame
        DataFrame with columns:
        ['Company', 'ISIN', 'ReportDate', 'category',
         'NumberOfShareholders', 'NumberOfShares', 'ShareholdingAsAPercentageOfTotalNumberOfShares']
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.nseindia.com"
    }

    # Fetch XML content
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Failed to fetch XML. HTTP {res.status_code}")

    # --- Extract metadata (Company, ISIN, Date) using BeautifulSoup ---
    soup = BeautifulSoup(res.text, "lxml-xml")

    def get_tag_value(tag_name):
        tag = soup.find(tag_name)
        return tag.text.strip() if tag else None

    company = get_tag_value("NameOfTheCompany")
    isin = get_tag_value("ISIN")
    report_date = get_tag_value("DateOfReport")

    # --- Parse detailed shareholding data using lxml ---
    parser = etree.XMLParser(recover=True)
    tree = etree.parse(BytesIO(res.content), parser)
    root = tree.getroot()

    ns = root.nsmap
    if None in ns:
        ns["default"] = ns.pop(None)

    # Extract all shareholding tags
    data = []
    for element in root.iter():
        tag_name = etree.QName(element).localname
        ns_uri = etree.QName(element).namespace
        if ns_uri and "in-bse-shp" in ns_uri:
            context = element.attrib.get("contextRef") or element.attrib.get("contextref")
            value = element.text.strip() if element.text else None
            data.append({
                "tag": tag_name,
                "contextref": context,
                "value": value
            })

    df = pd.DataFrame(data)

    # Extract context-category mapping
    contexts = []
    for ctx in root.findall(".//xbrli:context", namespaces=ns):
        ctx_id = ctx.attrib.get("id")
        member = ctx.find(".//xbrldi:explicitMember", namespaces=ns)
        if member is not None:
            category = member.text.split(":")[-1].replace("Member", "")
            contexts.append({"context_id": ctx_id, "category": category})

    context_df = pd.DataFrame(contexts)

    # Merge facts with category info
    merged_df = pd.merge(df, context_df, left_on="contextref", right_on="context_id", how="left")

    # Filter relevant metrics
    key_metrics = [
        "NumberOfShareholders",
        "NumberOfShares",
        "ShareholdingAsAPercentageOfTotalNumberOfShares"
    ]
    filtered_df = merged_df[merged_df["tag"].isin(key_metrics)]

    # Pivot to table form
    final_df = (
        filtered_df
        .pivot_table(index="category", columns="tag", values="value", aggfunc="first")
        .reset_index()
    )

    # Add metadata
    final_df["Company"] = company
    final_df["ISIN"] = isin
    final_df["ReportDate"] = report_date

    # Arrange columns neatly
    final_df = final_df[
        ["Company", "ISIN", "ReportDate", "category",
         "NumberOfShareholders", "NumberOfShares", "ShareholdingAsAPercentageOfTotalNumberOfShares"]
    ]

    return final_df
