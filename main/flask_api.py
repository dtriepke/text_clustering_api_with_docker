#! /usr/bin/env python3
#-*- coding: utf-8 -*-
from flask import Flask, request, make_response, send_file
from stemming.porter2 import stem
import re
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
from io import BytesIO
import zipfile
import time
import numpy as np

app = Flask(__name__)


# TODO include nlkt as pre processing
# def clean_text(txt):
#     # Compilers
#     remove_special_character = re.compile(r'[^A-Za-z ]', re.IGNORECASE)
#     replace_num = re.compile(r'\d+', re.IGNORECASE)

#     txt = txt.lower()
#     txt = remove_special_character.sub('', txt)
#     txt = replace_num.sub('',txt)
#     txt = txt.split()

#     stop_words = set(stopwords.words('english'))
#     stemmer = SnowballStemmer('english')
#     lemmatizer = WordNetLemmatizer()
#     processed_txt = []
#     for word in txt:
#         if word in stop_words:
#             continue
#         word = stemmer.stem(word)
#         word = lemmatizer.lemmatize(word)
#         word = lemmatizer.lemmatize(word, 'v')
#         processed_txt.append(word)

#     txt = ' '.join(processed_txt)
    
#     return txt


def clean_text(txt):
    if txt:
        
        # Compilers
        remove_special_character = re.compile(r'[^A-Za-z ]', re.IGNORECASE)
        replace_num = re.compile(r'\d+', re.IGNORECASE)

        # Compile
        txt = txt.lower()
        txt = remove_special_character.sub('', txt)
        txt = replace_num.sub('',txt)
        txt = txt.split()

        # Stemmer
        txt = [stem(t) for t in txt]

        return ' '.join(txt)


@app.route('/cluster', methods = ['POST'])
def cluster():

    data = pd.read_csv(request.files["dataset"])

    unstructured = "txt"
    if 'col' in request.args:
        unstructured = request.args.get('col')

    no_clusters = 2
    if 'no_clusters' in request.args:
        no_clusters = request.args.get('no_clusters')


    # Fill NA with strg
    data = data.fillna("NULL")

    # Apply txt cleaning
    data['clean_txt'] = data[unstructured].apply(clean_text)

    # Vectorizer
    vectorizer = CountVectorizer(analyzer='word', stop_words = 'english')
    X = vectorizer.fit_transform(data['clean_txt'])

    # Cluster
    kmeans = KMeans(n_clusters=no_clusters, random_state = 87).fit(X)
    data['cluster_num'] = kmeans.fit_predict(X)

    # Remove cleaned text
    data = data.drop(['clean_txt'], axis = 1)
   
    # Output excel in a zip file
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    #data = pd.DataFrame({'Data': [10, 20, 30, 20, 15, 30, 45]})
    data.to_excel(writer, sheet_name = 'clusters')

    # Add clusters' top keywords
    clusters = []
    for i in range(np.shape(kmeans.cluster_centers_)[0]):
        data_cluster = pd.concat([pd.Series(vectorizer.get_feature_names()),
                                  pd.DataFrame(kmeans.cluster_centers_[i])], axis=1)
        data_cluster.columns = ['keywords', 'weights']
        data_cluster = data_cluster.sort_values(by=['weights'], ascending=False)
        data_clust = data_cluster.head(n=10)['keywords'].tolist()
        clusters.append(data_clust)
    
    pd.DataFrame(clusters).to_excel(writer, sheet_name='Top_Keywords', encoding='utf-8')


    # Pivot
    data_pivot = data.groupby(['cluster_num'], as_index=False).size()
    data_pivot.name = 'size'
    data_pivot = data_pivot.reset_index()
    data_pivot.to_excel(writer, sheet_name='Cluster_Report', 
                  encoding='utf-8', index=False)

    # Add chart
    workbook = writer.book
    worksheet = writer.sheets['Cluster_Report']
    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
            'values': '=Cluster_Report!$B$2:$B'+str(no_clusters+1)
            })
    worksheet.insert_chart('D2', chart)
    

    writer.save()

    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, "w") as zf:
        names = ["cluster_output.xlsx"]
        files = [output]
        for i in range(len(names)):
            data = zipfile.ZipInfo(names[i])
            data.date_time = time.localtime(time.time())[:6]
            data.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(data, files[i].getvalue())
    memory_file.seek(0)

    response = make_response(send_file(memory_file, as_attachment=True, attachment_filename='cluster_output.zip'))
    response.headers['Content-Disposition'] = 'attachement;filename=cluster_output.zip'
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response


if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)