def build_target_body_from_offer(offer: dict, best_order: float):
    offer = offer[0]
    if 'exterior' in offer['extra']:
        return {
                "Amount": "1",
                "Price": {
                    "Currency": "USD",
                    "Amount": best_order
                },
                "Attributes": [
                    {
                        "Name": "name",
                        "Value": offer['extra']['name']
                    },
                    {
                        'Name': "title",
                        'Value': offer['title']
                    },
                    {
                        "Name": "category",
                        "Value": offer['extra']['category']
                    },
                    {
                       'Name': "exterior",
                       'Value': offer['extra']['exterior']
                    },
                    {
                        'Name': 'gameId',
                        'Value': offer['gameId']
                    },
                    {
                        'Name': 'categoryPath',
                        'Value': offer['extra']['categoryPath']
                    },
                    {
                        'Name': 'image',
                        'Value': offer['image']
                    },
                ]
            }

    else:
        return {
                    "Amount": "1",
                    "Price": {
                        "Currency": "USD",
                        "Amount": best_order
                    },
                    "Attributes": [
                        {
                            "Name": "name",
                            "Value": offer['extra']['name']
                        },
                        {
                            'Name': "title",
                            'Value': offer['title']
                        },
                        {
                            "Name": "category",
                            "Value": offer['extra']['category']
                        },
                        {
                            'Name': 'gameId',
                            'Value': offer['gameId']
                        },
                        {
                            'Name': 'categoryPath',
                            'Value': offer['extra']['categoryPath']
                        },
                        {
                            'Name': 'image',
                            'Value': offer['image']
                        },
                    ]
                }
