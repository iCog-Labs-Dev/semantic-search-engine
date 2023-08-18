# Format the prompt to include the query and some context
def format_prompt(query, context):
  return '''
    ### Messages:
    {context}

    ### Question:
    {query}
    '''.format(context=context, query=query)