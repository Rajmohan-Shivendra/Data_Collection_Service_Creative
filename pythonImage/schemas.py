aws_review_schema = {

    "properties":{
        "review_id": {"type":"string"},
        "reviewer_name": {"type": "string"},
        "reviewer_link": {"type": "string"},
        "rating": {"type": "integer"},  
        "review_title": {"type": "string"},
        "review_date": {"type": "string"},
        "review_description": {"type": "string"}
    },
    "required": ['review_id','reviewer_name','reviewer_link','rating','review_title','review_date','review_description'],
}