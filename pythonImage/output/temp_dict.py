data_dict = {
    'Reviewer Name': {
        'tag': 'span',
        'selector': {'class': 'a-profile-content'}
    },
    'Reviewer ID': {
        'tag': 'a',
        'selector': {'href_contains': '/gp/customer-reviews/'}
    },
    'Review Title': {
        'tag': 'span',
        'selector': {'id': 'review-title'}
    },
    'Review Body': {
        'tag': 'span',
        'selector': {'id': 'review-body'}
    },
    'Review Rating': {
        'tag': 'span',
        'selector': {'id': 'review-star-rating'}
    },
    'Review Date': {
        'tag': 'span',
        'selector': {'id': 'customer_review-R'}
    },
    'Reviewer Amazon Account': {
        'tag': 'a',
        'selector': {'href_contains': '/gp/profile/amzn1.account.'}
    }
}