import os
import time
import logging
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sec_api import QueryApi
from lxml import etree

load_dotenv()
logging.basicConfig(level=logging.INFO)

SEC_HEADERS = {
    "User-Agent": "Spandan (spandanmanoj@gmail.com)",  # replace with your real email
    "Accept-Encoding": "gzip, deflate",
    "Host": "www.sec.gov"
}


class SECAgent:
    def __init__(self):
        self.api_key = os.getenv("SEC_API_KEY")
        self.query_api = QueryApi(api_key=self.api_key)

    def fetch_last_24h_filings(self, lookback_days: int = 7):

        try:

            logging.info("Fetching SEC filings for last 7 days...")  
            # updated log

            now = datetime.utcnow()

            yesterday = now - timedelta(days=lookback_days)   # ✅ changed from days=1 to days=7

            query = {
                "query": {
                    "query_string": {
                        "query": f'formType:"4" AND filedAt:[{yesterday.isoformat()} TO {now.isoformat()}]'
                    }
                },
                "from": "0",
                "size": "50",
                "sort": [{"filedAt": {"order": "desc"}}]
            }

            response = self.query_api.get_filings(query)
            filings = response.get("filings", [])

            logging.info(f"Fetched {len(filings)} filings")
            return filings

        except Exception as e:
            logging.error(f"Error fetching SEC data: {e}")
            return []

    def get_correct_xml_url(self, docs):
        for doc in docs:
            url = doc.get("documentUrl", "")
            if "xsl" in url:
                continue
            if url.endswith(".xml"):
                return url
        return None

    def _get_value(self, element, tag):
        node = element.find(f".//{tag}")
        if node is None:
            return None

        value_node = node.find("value")
        if value_node is not None and value_node.text:
            try:
                return float(value_node.text.strip())
            except:
                return None

        if node.text:
            try:
                return float(node.text.strip())
            except:
                return None

        return None

    def extract_transactions(self, filings):
        results = []

        for filing in filings:
            try:
                ticker = filing.get("ticker")
                if not ticker:
                    continue

                docs = filing.get("documentFormatFiles", [])
                xml_url = self.get_correct_xml_url(docs)

                if not xml_url:
                    continue

                logging.info(f"Fetching XML for {ticker}")

                try:
                    response = requests.get(xml_url, headers=SEC_HEADERS, timeout=10)
                    response.raise_for_status()
                except Exception as e:
                    logging.warning(f"Request failed for {ticker}: {e}")
                    continue

                time.sleep(0.15)

                parser = etree.XMLParser(recover=True)
                root = etree.fromstring(response.content, parser)

                # Remove namespaces
                for elem in root.iter():
                    if not hasattr(elem.tag, "find"):
                        continue
                    i = elem.tag.find("}")
                    if i >= 0:
                        elem.tag = elem.tag[i + 1:]

                etree.cleanup_namespaces(root)

                transactions = root.findall(".//nonDerivativeTransaction")
                transactions += root.findall(".//derivativeTransaction")

                for tx in transactions:
                    try:
                        shares = self._get_value(tx, "transactionShares")

                        price = self._get_value(tx, "transactionPricePerShare")
                        if price is None:
                            price = self._get_value(tx, "exercisePrice")
                        if price is None:
                            price = 0.0

                        if shares is None:
                            continue

                        value = shares * price

                        if value < 1000 and price > 0:
                            continue

                        tx_code_node = tx.find(".//transactionCode")
                        tx_code = tx_code_node.text.strip() if tx_code_node is not None and tx_code_node.text else "?"

                        sec_title_node = tx.find(".//securityTitle/value")
                        sec_title = sec_title_node.text.strip() if sec_title_node is not None and sec_title_node.text else "?"

                        date_node = tx.find(".//transactionDate/value")
                        tx_date = date_node.text.strip() if date_node is not None and date_node.text else "?"

                        results.append({
                            "ticker": ticker,
                            "tx_code": tx_code,
                            "security": sec_title,
                            "date": tx_date,
                            "shares": shares,
                            "price": price,
                            "value": value,
                        })

                    except Exception as e:
                        logging.debug(f"Error parsing transaction: {e}")
                        continue

            except Exception as e:
                logging.warning(f"Error processing filing: {e}")
                continue

        results.sort(key=lambda x: x["value"], reverse=True)
        logging.info(f"Extracted {len(results)} transactions")

        return results


# ✅ STEP 2 FUNCTION
def get_top_5_tickers(transactions):
    ticker_map = {}

    for tx in transactions:
        ticker = tx["ticker"]

        if ticker not in ticker_map or tx["value"] > ticker_map[ticker]["value"]:
            ticker_map[ticker] = tx

    unique_transactions = list(ticker_map.values())
    unique_transactions.sort(key=lambda x: x["value"], reverse=True)

    return unique_transactions[:5]
