import pandas as pd
import utils.llm as llm
import sys
import streamlit as st

def match_products_with_search(final_df):
    with st.status("Starting the matching process...", expanded=True) as status:
        not_matched_df = pd.DataFrame(columns=['ean', 'product', 'cost'])

        # Iterate over each group, including the group name (search_term)
        for search_term, group in final_df.groupby('search_term'):
            # extract item names into an array
            item_names = group['item_name'].tolist()

            best_match = evaluate_match(search_term, item_names)

            if best_match == 'No match':
                st.markdown(f":red[No Match: {search_term}]")
            if best_match != 'No match':
                st.markdown(f":green[Match Found: {search_term}]")
            
            # if no match add to an array to retry later
            if best_match and "No match" in best_match:
                not_matched_df = pd.concat([not_matched_df, pd.DataFrame(
                    [{'UPC/EAN': group['ean'].iloc[0], 'product': search_term, 'cost': group['cost'].iloc[0]}])], ignore_index=True)
                
            # Mark the best match in the DataFrame
            # Create a new column 'is_best_match' and set it to True where the item_name matches the best_match for the search_term
            final_df.loc[(final_df['search_term'] == search_term) & (
                final_df['item_name'] == best_match), 'is_best_match'] = True
            # Optionally, set 'is_best_match' to False where it is not the best match for clarity
            final_df.loc[(final_df['search_term'] == search_term) & (
                final_df['item_name'] != best_match), 'is_best_match'] = False
    status.update(label="Match process complete!", state="complete", expanded=False)
    return final_df, not_matched_df


def evaluate_match(search_term, item_names):
    # Construct a prompt asking if the item_name matches the search_term
    prompt = """"
    The search term is: """ + search_term + """
    
    The list of items is: 
    """
    for item_name in item_names:
        prompt += item_name + ", "
    prompt += """

    Pay attention to the measurement units and use them to determine the best match for the search term. Convert between metric and imperial units if necessary.
    Pay more attention to the description of the item and less to the measurement units. 
    Respond with the item name only. What is the best match for the search term? 
    """

    system_message = "You are a world class AI name matching expert. If you can't find a match, respond with 'No match'."

    response = llm.call_openai(prompt, system_message)
    return response