# (simple) NLP Clustering API with Docker
Production grade version of a unstructered text clustering application.


## API
The API serves with two endpoints:
 1. localhost:5000/cluster [POST]
    - Args: `col` specify the text column in your input data
    - Args: `no_clusters` specify the number of cluster for kmeans (default = 2)

The api based on `flask`. 

## Docker
For launching the application  with docker use the following commands:
```bash
$ docker pull continuumio/anaconda3   
$ docker build --tag nlp_clustering .    
$ docker run -p 0.0.0.0:5000:5000/tcp --name my_text_clustering_app nlp_clustering  
```



*The last command starts a new docker container*


***
**Credentials**  
This project based on the udemy course Deploy Machine Learning & NLP Models with Dockers (DevOps): https://www.udemy.com/course/deploy-data-science-nlp-models-with-docker-containers/
