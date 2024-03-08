# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st

import pandas as pd
import time
import utils.llm as llm
import utils.amazon as amazon
import match


def parse_output(ean, search, item_cost, items):
    asin = []
    ean_term = []
    search_term = []
    item_name = []
    cost = []
    package_quantity = []
    height = []
    length = []
    width = []
    weight = []

    # only use the first 3 items
    for item in items.json()["items"][:3]:
        # asin
        asin.append(item['asin'])

        # ean
        ean_term.append(ean)

        # search term
        search_term.append(search)

        # product name
        item_name.append(item['summaries'][0]['itemName'])

        # cost
        cost.append(item_cost)

        package_quantity_value = item['attributes'].get(
            'item_package_quantity')
        if package_quantity_value:
            package_quantity.append(
                package_quantity_value[0].get('value', 'N/A'))
        else:
            package_quantity.append('N/A')

        # dimensions in cm
        if item['dimensions'][0] and item['dimensions'][0].get('package'):
            dimensions = item['dimensions'][0]['package']
            if 'height' not in dimensions:
                height.append('N/A')
            else:
                height.append(round(dimensions['height']['value'] * 2.54, 2))
            if 'length' not in dimensions:
                length.append('N/A')
            else:
                length.append(round(dimensions['length']['value'] * 2.54, 2))
            if 'width' not in dimensions:
                width.append('N/A')
            else:
                width.append(round(dimensions['width']['value'] * 2.54, 2))
            if 'weight' not in dimensions:
                weight.append('N/A')
            else:
                weight.append(
                    round(dimensions['weight']['value'] * 0.453592, 2))
        else:
            height.append('N/A')
            length.append('N/A')
            width.append('N/A')
            weight.append('N/A')

    return pd.DataFrame(
        {
            'asin': asin,
            'ean': ean_term,
            'search_term': search_term,
            'item_name': item_name,
            'cost': cost,
            'package_quantity': package_quantity,
            'height': height,
            'length': length,
            'width': width,
            'weight': weight,
        })


def search_amazon(products_df, search_column='product', return_column='product'):
    # Initialize a list to store DataFrames
    dfs = []

    with st.status("Starting the search on Amazon...", expanded=True) as status:
        # Iterate through each product
        for index, row in products_df.iterrows():
            search_term = row[search_column]
            cost = row['cost']
            ean = str(row['UPC/EAN'])

            st.write(f"Searching for Product: {search_term}")
            df = []
            items = amazon.get_item_details_by_keyword(search_term)

            if items.json()['numberOfResults'] == 0:
                st.write(f"No results found for {search_term}")
            else:
                df = parse_output(ean, row[return_column], cost, items)
                # Append the DataFrame to the list
                dfs.append(df)

            if ean:
                st.write(f"Searching for UPC/EAN: {ean}")
                # sleep for 1 second to avoid throttling
                time.sleep(1)

                df = []
                items = amazon.get_item_details_by_gtin(ean)

                if items.json()['numberOfResults'] == 0:
                    st.write(f":red[No results found for {ean}]")
                else:
                    st.write(f":green[Found result(s) for {ean}]")
                    df = parse_output(ean, row[return_column], cost, items)
                    # Append the DataFrame to the list
                    dfs.append(df)

            # sleep for 1 second to avoid throttling
            time.sleep(1)

        # Update Streamlit state
        status.update(label="Amazon search complete!", state="complete", expanded=False)
        # Concatenate all DataFrames in the list into a single DataFrame
        final_df = pd.concat(dfs, ignore_index=True)
        return final_df

st.title('Ghost ASIN Scraper 👻')
st.caption('*This tool is used to confirm whether the ASINS/EAN we recieve are accurate. Note this is an internally built solution that may result with inaccurate results. Please use with discretion.*')
with st.sidebar:
    uploaded_file = st.file_uploader('CSV Uploader')


if uploaded_file is not None:

    # Read the CSV file into a DataFrame
    products_df = pd.read_csv(uploaded_file)

    # get the search results from Amazon
    final_df = search_amazon(products_df)

    # Export the final DataFrame to a new CSV file
    final_df.to_csv('data/products_with_amazon_searches.csv', index=False)

    # Find the best match
    final_df, not_matched_df = match.match_products_with_search(final_df)

    # if there are any non matched items, try again
    if len(not_matched_df) > 0:
        with st.status("Cleaning up search terms for unmatched items...", expanded=True) as status:
            for index, row in not_matched_df.iterrows():
                search_term = row['product']
                cost = row['cost']
                
                # Clean up the search term
                prompt = """"
                The search term is: """ + search_term + """
                
                Remove any references to sizing in ml / oz.
                Remove any reference to degrees °.
                Respond with the cleaned search term and nothing else.
                """

                clean_product = llm.call_openai(prompt)
                st.write(f"Original product: {search_term}\nCleaned product: {clean_product}")

                # add a new row to not_matched_df calledd cleaned_search_term
                not_matched_df.at[index, 'cleaned_product'] = clean_product
        status.update(label="Cleaning up search terms complete!", state="complete", expanded=False)
        # Search again
        not_matched_search_results_df = search_amazon(
            not_matched_df, "cleaned_product", "product")

        # Match again
        matched_retry_df, not_matched_remaining_df = match.match_products_with_search(
            not_matched_search_results_df)

        # Merge the matched and not matched DataFrames
        final_df = pd.concat([final_df, matched_retry_df])

    # Export the final DataFrame to a new CSV file
    final_csv_file_path = 'data/products_matched.csv'
    final_df = final_df[final_df['is_best_match']
                        == True].drop(columns=['is_best_match'])

    # deduplicate any entries in final_df
    final_df = final_df.drop_duplicates(subset=['search_term'], keep='first')

    @st.cache_data
    def convert_df(df):
        # IMPORTANT: Cache the conversion to prevent computation on every rerun
        return df.to_csv().encode('utf-8')

    # convert df to csv
    csv = convert_df(final_df)

    # download button
    st.download_button(
    "Download CSV",
    csv,
    "file.csv",
    "text/csv",
    key='download-csv'
    )