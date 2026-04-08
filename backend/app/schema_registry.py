ALLOWED_TYPES = {
    "product": {
        "required_fields": ["name", "description"],
        "schema_type": "Product",
    },
    "article": {
        "required_fields": ["name", "description"],
        "schema_type": "Article",
    },
    "webpage": {
        "required_fields": ["name", "description"],
        "schema_type": "WebPage",
    },
    "hotel": {
        "required_fields": ["name", "address"],
        "schema_type": "Hotel",
    },
}
