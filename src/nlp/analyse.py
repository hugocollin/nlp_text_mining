import pandas as pd
import numpy as np
from transformers import pipeline

class NLPAnalysis:
    def __init__(self):

        self.data = pd.DataFrame()
        self.model = None
        self.tokenizer = None

 
    def summarize_reviews(self, df):
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        all_reviews = ' '.join(df['review'].values)
        
        # Split the reviews into chunks of 1024 tokens
        max_chunk_length = 1024
        chunks = [all_reviews[i:i + max_chunk_length] for i in range(0, len(all_reviews), max_chunk_length)]
        
        nbr_chunks = 20
        if len(chunks) < nbr_chunks:
            nbr_chunks = len(chunks)
        sample_of_chunks_alea = np.random.choice(chunks, nbr_chunks)
        
        # Summarize each chunk and combine the summaries
        summaries = []
        print("nb chunks : " , len(chunks))
        for id, chunk in enumerate(sample_of_chunks_alea):
            print(f"Summarizing chunk {id} ...")
            summary = summarizer(chunk, max_length=60, min_length=40, do_sample=True)
            summaries.append(summary[0]['summary_text'])
            print(summary[0]['summary_text'])
        
        summary = ' '.join(summaries)
        return summary


