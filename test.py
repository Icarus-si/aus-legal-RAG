from rag.pipeline import load_vectorstore, get_rag_chain, ask_question

vs = load_vectorstore()
chain = get_rag_chain(vs)

result = ask_question(chain, 'Why did the delegate refuse the nomination application?')
print(result['answer'])
print('---SOURCES---')
for s in result['sources']:
    print(f"Case: {s['case']}, Page: {s['page']}")