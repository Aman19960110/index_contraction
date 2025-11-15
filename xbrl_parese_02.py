from bs4 import BeautifulSoup
import requests
import pandas as pd
from lxml import etree
from io import BytesIO

def parse_xbrl_shareholding(url: str) -> pd.DataFrame:
    """
    Parse NSE/BSE XBRL Shareholding Pattern XML and return category-wise shareholding DF.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://www.nseindia.com"
    }

    # Fetch XML content
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        raise Exception(f"Failed to fetch XML. HTTP {res.status_code}")

    # --- Extract metadata using BeautifulSoup ---
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

    # Extract all shareholding facts (NumberOfShares, etc.)
    data = []
    for element in root.iter():
        tag_name = etree.QName(element).localname
        ns_uri = etree.QName(element).namespace
        if ns_uri and "shp" in ns_uri:       # supports both NSE & BSE
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
    merged_df = pd.merge(df, context_df,
                         left_on="contextref", right_on="context_id", how="left")

    # Select only key metrics
    key_metrics = [
        "NumberOfShareholders",
        "NumberOfShares",
        "ShareholdingAsAPercentageOfTotalNumberOfShares"
    ]
    filtered_df = merged_df[merged_df["tag"].isin(key_metrics)]

    # Pivot to structured form
    final_df = (
        filtered_df
        .pivot_table(index="category", columns="tag", values="value", aggfunc="first")
        .reset_index()
    )

    # Add metadata
    final_df["Company"] = company
    final_df["ISIN"] = isin
    final_df["ReportDate"] = report_date

    return final_df


# -------------------------------------------------------
# ⭐ NEW FUNCTION → extract REQUIRED summary values only
# -------------------------------------------------------
def extract_summary_values(df: pd.DataFrame):

    # Convert shares to numeric
    df["NumberOfShares"] = pd.to_numeric(df["NumberOfShares"], errors="coerce")

    # ---- Correct NSE/BSE category names ----
    promoter_row = df[df["category"] == "ShareholdingOfPromoterAndPromoterGroup"]
    public_row = df[df["category"] == "PublicShareholding"]
    total_row = df[df["category"] == "ShareholdingPattern"]

    promoter_shares = promoter_row["NumberOfShares"].values[0]
    public_shares = public_row["NumberOfShares"].values[0]
    total_shares = total_row["NumberOfShares"].values[0]

    free_float_factor = public_shares / total_shares

    return {
        "promoter_shares": int(promoter_shares),
        "public_shares": int(public_shares),
        "total_shares": int(total_shares),
        "free_float_factor": round(free_float_factor, 4)
    }


# -------------------------------------------------------
# ⭐ Example Usage
# -------------------------------------------------------

url = "https://nsearchives.nseindia.com/corporate/xbrl/SHP_1544919_10102025115803_WEB.xml"

df = parse_xbrl_shareholding(url)
summary = extract_summary_values(df)

print(summary)
