from test import test_metrics

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama.llms import OllamaLLM

context_str='''
In the 19th and 20th century land was reclaimed from the sea to make use of the exposed fertile soils for agriculture through a process known as impoldering. 
The reclaimed land is now characterized by intensive grazing and cropland. 
This is a region where agriculture is the most important form of land use. 
However, the land needs to be regularly drained. 
Given the expected increase in precipitation in winter due to climate change, the corresponding increase in freshwater discharge needs to be managed. 
Furthermore, the periods when natural discharge into the sea oc-curs are likely to decrease – because of rising sea levels also caused by climate change. 
Consequently, in winter and spring, greater quantities of freshwater will need to be pumped into the sea rather than discharged naturally at the low or ebb tide. 
Specially embanked water retention polders will be required to temporarily impound water as part of a multifunctional approach to coastal zone management.
'''
template = """Use the following pieces of context to answer the question at the end.\n\n{context}\n\nQuestion: {question}\nHelpful Answer:"""
question = "What is impoldering?"
prompt = ChatPromptTemplate.from_template(template)

model_outputs = []
for model_type in ['qwen:0.5b', 'qwen']:
    model = OllamaLLM(model=model_type)

    chain = prompt | model

    model_output = chain.invoke({"question":question,"context": context_str})
    model_outputs.append(model_output)


test_metrics(model_outputs, context_str, question)
print('\n\n')


    